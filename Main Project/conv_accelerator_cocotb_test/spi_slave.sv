// ============================================================================
// spi_slave.sv
//
// SPI‐slave for conv‐accelerator Cocotb test (Icarus‐compatible).
//
// Final fixes applied here:
//   • Asynchronous CS reset for RX shift block so rx_byte_ready can pulse
//     even if CS deasserts immediately after the 8th bit.
//   • Capture full 8‐bit in rx_latched_byte when rx_bit_cnt==0, then pulse
//     rx_byte_ready for exactly one SCLK cycle.
//   • FSM now latches commands from rx_latched_byte (not rx_shift_reg).
//   • Sample MOSI on posedge sclk_spi (Mode 0).
//   • No async CS reset of the FSM—reset only at power‐up via initial block.
//   • Retained next_cmd_reg pattern, “start_to_wrapper_raw” naming, and
//     explicit genvar loops (with corrected parameter spelling).
// ============================================================================

module spi_slave (
    // SPI interface (Mode 0)
    input  wire        sclk_spi,        // SPI clock from master
    input  wire        cs_n_spi,        // Chip‐select (active low)
    input  wire        mosi_spi,        // Master → Slave data
    output reg         miso_spi,        // Slave → Master data

    // Convolution‐wrapper interface (main clock domain)
    input  wire        clk_main,             // 100 MHz main clock (10 ns)
    input  wire        rst_n_main,           // Active‐low reset, sync to clk_main
    output reg         start_to_wrapper_raw, // One‐cycle SCLK‐domain pulse
    output     [25*8-1:0]       patch_to_wrapper,    // 25 bytes of patch
    output     [(5*5*16*5)-1:0] weights_to_wrapper,  // 250 bytes of weights
    output     [5*16-1:0]       biases_to_wrapper,   // 10 bytes of biases
    input  wire [5*16-1:0]       results_from_wrapper, // 10 bytes of results
    input  wire        done_from_wrapper,    // Pulses high 1 clk_main when done
    input  wire        busy_from_wrapper,    // High while conv is processing

    // Debug outputs (for Cocotb logging)
    output reg [3:0]   spi_fsm_current_state_debug,   // Current FSM state
    output reg [7:0]   spi_current_cmd_reg_debug,     // Latched command
    output reg         spi_trigger_wrapper_pulse_debug// One‐cycle pulse each SCLK when start issued
);

    // =========================================================================
    // Parameter / command codes (must match test_spi_accelerator.py)
    // =========================================================================
    localparam byte unsigned CMD_WRITE_WEIGHTS = 8'h01;
    localparam byte unsigned CMD_WRITE_PATCH   = 8'h02;
    localparam byte unsigned CMD_WRITE_BIASES  = 8'h03;
    localparam byte unsigned CMD_START_PROC    = 8'h10;
    localparam byte unsigned CMD_READ_STATUS   = 8'h20;
    localparam byte unsigned CMD_READ_RESULTS  = 8'h30;

    localparam int unsigned WEIGHTS_BYTES = 250;  // 5 kernels × 25 weights × 2 bytes
    localparam int unsigned PATCH_BYTES   = 25;   // 5×5 patch (1 byte each)
    localparam int unsigned BIASES_BYTES  = 10;   // 5 biases × 2 bytes
    localparam int unsigned RESULTS_BYTES = 10;   // 5 results × 2 bytes

    // =========================================================================
    // FSM state enumeration
    // =========================================================================
    typedef enum logic [3:0] {
        S_IDLE               = 4'd0,
        S_DECODE_CMD         = 4'd2,
        S_RX_DATA_WAIT_BYTE  = 4'd3,
        S_RX_DATA_STORE      = 4'd4,
        S_TRIGGER_WRAPPER    = 4'd5,
        S_WAIT_WRAPPER_BUSY  = 4'd6,
        S_WAIT_WRAPPER_DONE  = 4'd7,
        S_LATCH_RESULTS      = 4'd8,
        S_TX_SETUP           = 4'd9,
        S_TX_DATA_SHIFTING   = 4'd10,
        S_TX_DATA_NEXT       = 4'd11
    } fsm_state_t;

    // =========================================================================
    // Internal signals / registers
    // =========================================================================
    fsm_state_t       current_state, next_state;

    // Separate “current” and “next” for the command register
    reg [7:0]         current_cmd_reg, next_cmd_reg;

    // Count how many data bytes we expect to RX or TX
    reg [15:0]        data_bytes_expected_count;
    reg [15:0]        data_byte_io_counter;

    // RX shift logic: down‐counter from 7→0, shift in MSB‐first
    reg [7:0]         rx_shift_reg;     // partial shift‐in
    reg [7:0]         rx_latched_byte;  // captures full 8-bit when ready
    reg [2:0]         rx_bit_cnt;       // counts 7→0
    reg               rx_byte_ready;    // pulses high for 1 SCLK when rx_latched_byte is valid

    // TX shift logic: shift out on MISO at falling SCLK
    reg [7:0]         tx_shift_reg;     // current byte being shifted out
    reg [2:0]         tx_bit_cnt;       // counts 7→0
    reg               tx_byte_sent;     // pulses high for 1 SCLK when a full byte went out

    // Memories for incoming data
    reg [7:0]         patch_mem   [0:PATCH_BYTES-1];
    reg [7:0]         weights_mem [0:WEIGHTS_BYTES-1];
    reg [7:0]         biases_mem  [0:BIASES_BYTES-1];

    // Memory for latched results
    reg [7:0]         results_mem [0:RESULTS_BYTES-1];

    // =========================================================================
    // SECTION 1: RX SHIFT—assemble bytes from MOSI on rising SCLK
    // =========================================================================
    //   • As soon as cs_n_spi goes high, asynchronously clear rx_bit_cnt→7,
    //     rx_shift_reg→0, rx_latched_byte→0, and rx_byte_ready→0.
    //   • Otherwise, on each posedge sclk_spi (CS low), shift mosi_spi into
    //     rx_shift_reg[rx_bit_cnt]. If rx_bit_cnt==0, form full byte in
    //     rx_latched_byte, assert rx_byte_ready=1 for that cycle, wrap
    //     rx_bit_cnt→7. Else, decrement rx_bit_cnt and clear rx_byte_ready.
    //   • FSM decodes commands from rx_latched_byte when rx_byte_ready=1.
    always_ff @(posedge sclk_spi or posedge cs_n_spi) begin
        if (cs_n_spi) begin
            rx_bit_cnt      <= 3'd7;
            rx_shift_reg    <= 8'h00;
            rx_latched_byte <= 8'h00;
            rx_byte_ready   <= 1'b0;
        end else begin
            rx_shift_reg[rx_bit_cnt] <= mosi_spi;
            if (rx_bit_cnt == 3'd0) begin
                // Completed 8 bits: capture and pulse ready
                rx_latched_byte <= {rx_shift_reg[6:0], mosi_spi};
                rx_byte_ready   <= 1'b1;
                rx_bit_cnt      <= 3'd7;
            end else begin
                rx_byte_ready <= 1'b0;
                rx_bit_cnt    <= rx_bit_cnt - 3'd1;
            end
        end
    end

    // =========================================================================
    // SECTION 2: TX SHIFT—drive MISO on each falling SCLK (Mode 0)
    // =========================================================================
    always_ff @(negedge sclk_spi or posedge cs_n_spi) begin
        if (cs_n_spi) begin
            miso_spi     <= 1'b0;
            tx_bit_cnt   <= 3'd7;
            tx_byte_sent <= 1'b0;
        end else begin
            miso_spi <= tx_shift_reg[tx_bit_cnt];
            if (tx_bit_cnt == 3'd0) begin
                tx_byte_sent <= 1'b1;
                tx_bit_cnt   <= 3'd7;
            end else begin
                tx_byte_sent <= 1'b0;
                tx_bit_cnt   <= tx_bit_cnt - 3'd1;
            end
        end
    end

    // =========================================================================
    // SECTION 3: FSM—clocked on posedge sclk_spi (no async CS reset)
    // =========================================================================
    //   • Initialize only via initial block so CS_n_spi does not reset FSM.
    //   • On each posedge sclk_spi, latch next_state→current_state and
    //     next_cmd_reg→current_cmd_reg.
    initial begin
        current_state             = S_IDLE;
        current_cmd_reg           = 8'h00;
        data_bytes_expected_count = 16'd0;
        data_byte_io_counter      = 16'd0;
        tx_shift_reg              = 8'h00;
        spi_trigger_wrapper_pulse_debug = 1'b0;
        spi_current_cmd_reg_debug     = 8'h00;
        spi_fsm_current_state_debug   = S_IDLE;
    end

    always_ff @(posedge sclk_spi) begin
        current_state   <= next_state;
        current_cmd_reg <= next_cmd_reg;
        spi_current_cmd_reg_debug    <= next_cmd_reg;
        spi_fsm_current_state_debug  <= next_state;
    end

    // =========================================================================
    // SECTION 4: FSM combinational—determine next_state, next_cmd_reg, outputs
    // =========================================================================
    always_comb begin
        next_state      = current_state;
        next_cmd_reg    = current_cmd_reg;

        // Default outputs
        start_to_wrapper_raw          = 1'b0;
        spi_trigger_wrapper_pulse_debug = 1'b0;

        case (current_state)
            // --------------------------------------------------------
            S_IDLE: begin
                // Wait for a full command byte (rx_byte_ready=1)
                if (rx_byte_ready) begin
                    next_cmd_reg = rx_latched_byte;  // latch the command
                    next_state   = S_DECODE_CMD;
                end else begin
                    next_state = S_IDLE;
                end
            end

            // --------------------------------------------------------
            S_DECODE_CMD: begin
                case (current_cmd_reg)
                    CMD_WRITE_WEIGHTS: begin
                        data_bytes_expected_count = WEIGHTS_BYTES;
                        data_byte_io_counter      = 16'd0;
                        next_state                = S_RX_DATA_WAIT_BYTE;
                    end

                    CMD_WRITE_PATCH: begin
                        data_bytes_expected_count = PATCH_BYTES;
                        data_byte_io_counter      = 16'd0;
                        next_state                = S_RX_DATA_WAIT_BYTE;
                    end

                    CMD_WRITE_BIASES: begin
                        data_bytes_expected_count = BIASES_BYTES;
                        data_byte_io_counter      = 16'd0;
                        next_state                = S_RX_DATA_WAIT_BYTE;
                    end

                    CMD_START_PROC: begin
                        next_state = S_TRIGGER_WRAPPER;
                    end

                    CMD_READ_STATUS: begin
                        data_bytes_expected_count = 16'd1;
                        data_byte_io_counter      = 16'd0;
                        tx_shift_reg              = {6'b0, done_from_wrapper, busy_from_wrapper};
                        next_state                = S_TX_SETUP;
                    end

                    CMD_READ_RESULTS: begin
                        data_bytes_expected_count = RESULTS_BYTES;
                        data_byte_io_counter      = 16'd0;
                        tx_shift_reg              = results_mem[0];  // MSB first
                        next_state                = S_TX_SETUP;
                    end

                    default: begin
                        next_state = S_IDLE;
                    end
                endcase
            end

            // --------------------------------------------------------
            S_RX_DATA_WAIT_BYTE: begin
                if (rx_byte_ready) begin
                    next_state = S_RX_DATA_STORE;
                end else begin
                    next_state = S_RX_DATA_WAIT_BYTE;
                end
            end

            // --------------------------------------------------------
            S_RX_DATA_STORE: begin
                case (current_cmd_reg)
                    CMD_WRITE_WEIGHTS: begin
                        weights_mem[data_byte_io_counter] = rx_latched_byte;
                    end

                    CMD_WRITE_PATCH: begin
                        patch_mem[data_byte_io_counter] = rx_latched_byte;
                    end

                    CMD_WRITE_BIASES: begin
                        biases_mem[data_byte_io_counter] = rx_latched_byte;
                    end

                    default: begin
                        // Should not occur
                    end
                endcase

                data_byte_io_counter = data_byte_io_counter + 16'd1;
                if (data_byte_io_counter + 16'd1 < data_bytes_expected_count) begin
                    next_state = S_RX_DATA_WAIT_BYTE;
                end else begin
                    next_state = S_IDLE;
                end
            end

            // --------------------------------------------------------
            S_TRIGGER_WRAPPER: begin
                start_to_wrapper_raw           = 1'b1;
                spi_trigger_wrapper_pulse_debug = 1'b1;
                next_state                      = S_WAIT_WRAPPER_BUSY;
            end

            // --------------------------------------------------------
            S_WAIT_WRAPPER_BUSY: begin
                if (busy_from_wrapper) begin
                    next_state = S_WAIT_WRAPPER_DONE;
                end else begin
                    next_state = S_WAIT_WRAPPER_BUSY;
                end
            end

            // --------------------------------------------------------
            S_WAIT_WRAPPER_DONE: begin
                if (done_from_wrapper) begin
                    next_state = S_LATCH_RESULTS;
                end else begin
                    next_state = S_WAIT_WRAPPER_DONE;
                end
            end

            // --------------------------------------------------------
            S_LATCH_RESULTS: begin
                next_state = S_IDLE;
            end

            // --------------------------------------------------------
            S_TX_SETUP: begin
                next_state = S_TX_DATA_SHIFTING;
            end

            // --------------------------------------------------------
            S_TX_DATA_SHIFTING: begin
                if (tx_byte_sent) begin
                    data_byte_io_counter = data_byte_io_counter + 16'd1;
                    if (data_byte_io_counter + 16'd1 < data_bytes_expected_count) begin
                        tx_shift_reg = results_mem[data_byte_io_counter + 1];
                        next_state   = S_TX_DATA_NEXT;
                    end else begin
                        next_state = S_IDLE;
                    end
                end else begin
                    next_state = S_TX_DATA_SHIFTING;
                end
            end

            // --------------------------------------------------------
            S_TX_DATA_NEXT: begin
                next_state = S_TX_SETUP;
            end

            // --------------------------------------------------------
            default: begin
                next_state = S_IDLE;
            end
        endcase
    end

    // =========================================================================
    // SECTION 5: PACK/UNPACK via GENERATE (no variable part‐selects)
    // =========================================================================

    // Pack patch_mem[0..24] → patch_to_wrapper[199:0] (MSB first)
    genvar gi1;
    generate
        for (gi1 = 0; gi1 < PATCH_BYTES; gi1 = gi1 + 1) begin : PKG_PATCH
            assign patch_to_wrapper[((PATCH_BYTES - 1 - gi1)*8) +: 8] = patch_mem[gi1];
        end
    endgenerate

    // Pack weights_mem[0..249] → weights_to_wrapper[1999:0] (MSB first)
    genvar gi2;
    generate
        for (gi2 = 0; gi2 < WEIGHTS_BYTES; gi2 = gi2 + 1) begin : PKG_WEIGHTS
            assign weights_to_wrapper[((WEIGHTS_BYTES - 1 - gi2)*8) +: 8] = weights_mem[gi2];
        end
    endgenerate

    // Pack biases_mem[0..9] → biases_to_wrapper[79:0] (MSB first)
    genvar gi3;
    generate
        for (gi3 = 0; gi3 < BIASES_BYTES; gi3 = gi3 + 1) begin : PKG_BIASES
            assign biases_to_wrapper[((BIASES_BYTES - 1 - gi3)*8) +: 8] = biases_mem[gi3];
        end
    endgenerate

    // Unpack results_from_wrapper[79:0] → results_mem[0..9] (MSB first)
    genvar gi4;
    generate
        for (gi4 = 0; gi4 < RESULTS_BYTES; gi4 = gi4 + 1) begin : UNPKG_RESULTS
            assign results_mem[gi4] = results_from_wrapper[((RESULTS_BYTES - 1 - gi4)*8) +: 8];
        end
    endgenerate

endmodule
