// ============================================================================
// accelerator_system.sv
//
// Top-level that instantiates spi_slave (with a raw SCLK-domain pulse) and
// a two-FF synchronizer to stretch that pulse into clk_main domain before
// handing off to conv5x5_wrapper.
// ============================================================================

module accelerator_system (
    // SPI pins
    input  wire        sclk_spi,
    input  wire        cs_n_spi,
    input  wire        mosi_spi,
    output wire        miso_spi,

    // Main clock and reset for conv wrapper
    input  wire        clk_main,      // 100 MHz main clock
    input  wire        rst_n_main     // Active-low reset
);

    // ------------------------------------------------------------
    // Internal nets for wrapper interface
    // ------------------------------------------------------------
    wire [25*8-1:0]        patch_pixels_internal;    // 25 bytes flattened
    wire [(5*5*16*5)-1:0]  all_weights_internal;     // 250 bytes flattened
    wire [5*16-1:0]        all_biases_internal;      // 10 bytes flattened
    wire [5*16-1:0]        results_internal;         // 10 bytes flattened
    wire                   processing_done_internal; // Done flag from conv
    wire                   busy_internal;            // Busy flag from conv

    // ------------------------------------------------------------
    // Synchronizer for start pulse from SPI slave
    // ------------------------------------------------------------
    wire                   start_to_wrapper_raw;      // Raw SCLK-domain pulse
    reg                    start_raw_d1, start_raw_d2;
    reg                    start_proc_internal;       // Synchronized, one‐clk_main pulse

    // ------------------------------------------------------------
    // Generate a synchronized, one‐clk_main‐wide pulse from the raw SCLK-domain pulse
    // ------------------------------------------------------------
    always_ff @(posedge clk_main or negedge rst_n_main) begin
        if (!rst_n_main) begin
            start_raw_d1        <= 1'b0;
            start_raw_d2        <= 1'b0;
            start_proc_internal <= 1'b0;
        end else begin
            // Shift in raw pulse
            start_raw_d1        <= start_to_wrapper_raw;
            start_raw_d2        <= start_raw_d1;
            // If raw went from 0→1, assert start_proc_internal for one clk_main cycle
            start_proc_internal <= start_raw_d1 & ~start_raw_d2;
        end
    end

    // ------------------------------------------------------------
    // Instantiate SPI slave
    // ------------------------------------------------------------
    spi_slave u_spi_slave (
        .sclk_spi                         (sclk_spi),
        .cs_n_spi                         (cs_n_spi),
        .mosi_spi                         (mosi_spi),
        .miso_spi                         (miso_spi),

        .clk_main                         (clk_main),
        .rst_n_main                       (rst_n_main),
        .start_to_wrapper_raw             (start_to_wrapper_raw),      // raw SCLK-domain pulse

        .patch_to_wrapper                 (patch_pixels_internal),
        .weights_to_wrapper               (all_weights_internal),
        .biases_to_wrapper                (all_biases_internal),

        .results_from_wrapper             (results_internal),
        .done_from_wrapper                (processing_done_internal),
        .busy_from_wrapper                (busy_internal),

        .spi_fsm_current_state_debug      (spi_fsm_current_state_debug),
        .spi_current_cmd_reg_debug        (spi_current_cmd_reg_debug),
        .spi_trigger_wrapper_pulse_debug  (spi_trigger_wrapper_pulse_debug)
    );

    // ------------------------------------------------------------
    // Instantiate conv5x5_wrapper, using the synchronized pulse
    // ------------------------------------------------------------
    conv5x5_wrapper u_conv5x5_wrapper (
        .clk               (clk_main),
        .rst_n             (rst_n_main),
        .i_start_processing(start_proc_internal),
        .i_patch_pixels_flat(patch_pixels_internal),
        .i_all_weights_flat(all_weights_internal),
        .i_all_biases_flat (all_biases_internal),
        .o_results_flat    (results_internal),
        .o_processing_done (processing_done_internal),
        .o_busy            (busy_internal)
    );

endmodule
