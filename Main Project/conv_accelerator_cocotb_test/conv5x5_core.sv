`timescale 1ns/1ps

module conv5x5_core (
    input  wire                          clk,
    input  wire                          rst_n,
    input  wire                          start_channel_proc,
    input  wire [INPUT_WIDTH-1:0]      patch_pixels [0:PATCH_DIM-1][0:PATCH_DIM-1],
    input  wire signed [WEIGHT_WIDTH-1:0] kernel_weights [0:PATCH_DIM-1][0:PATCH_DIM-1],
    input  wire signed [BIAS_WIDTH-1:0]  bias_val,
    output logic signed [OUTPUT_WIDTH-1:0] channel_output_value,
    output logic                         channel_output_valid,
    output logic                         busy
);

    localparam PATCH_DIM             = 5;
    localparam NUM_KERNEL_ELEMENTS   = PATCH_DIM * PATCH_DIM;
    localparam INPUT_WIDTH           = 8;
    localparam WEIGHT_WIDTH          = 16;
    localparam BIAS_WIDTH            = 16;
    localparam PRODUCT_WIDTH         = INPUT_WIDTH + WEIGHT_WIDTH;
    localparam ACC_WIDTH             = 32;
    localparam OUTPUT_WIDTH          = 16;
    localparam SHIFT_AMOUNT          = 8;

    typedef enum logic [2:0] {
        S_IDLE,
        S_LOAD_INPUTS,
        S_MAC_INIT,
        S_MAC_COMPUTE,
        S_ADD_BIAS,
        S_SHIFT_RELU,
        S_DONE
    } state_t;

    state_t current_state, next_state;

    logic [INPUT_WIDTH-1:0]         patch_pixels_reg [0:PATCH_DIM-1][0:PATCH_DIM-1];
    logic signed [WEIGHT_WIDTH-1:0] kernel_weights_reg [0:PATCH_DIM-1][0:PATCH_DIM-1];
    logic signed [BIAS_WIDTH-1:0]   bias_val_reg;

    logic signed [ACC_WIDTH-1:0]      mac_accumulator;
    logic signed [PRODUCT_WIDTH-1:0]  current_product_comb;
    logic signed [PRODUCT_WIDTH-1:0]  product_reg_pipelined;
    logic [4:0]                       mac_count;

    logic signed [ACC_WIDTH-1:0]      accumulator_with_bias;
    logic signed [ACC_WIDTH-1:0]      shifted_value;

    always_ff @(posedge clk or negedge rst_n) begin
        integer r, c;
        if (!rst_n) begin
            current_state         <= S_IDLE;
            busy                  <= 1'b0;
            channel_output_valid  <= 1'b0;
            mac_count             <= 5'd0;
            mac_accumulator       <= '0; 
            product_reg_pipelined <= '0; 
            for (r = 0; r < PATCH_DIM; r = r + 1) begin
                for (c = 0; c < PATCH_DIM; c = c + 1) begin
                    patch_pixels_reg[r][c]   <= {INPUT_WIDTH{1'b0}};
                    kernel_weights_reg[r][c] <= {WEIGHT_WIDTH{1'b0}};
                end
            end
            bias_val_reg <= {BIAS_WIDTH{1'b0}};
        end else begin
            current_state        <= next_state;
            channel_output_valid <= 1'b0; 

            if (current_state == S_IDLE && next_state != S_IDLE) begin
                busy <= 1'b1;
            end else if (current_state == S_DONE && next_state == S_IDLE) begin
                busy <= 1'b0;
            end

            case (current_state)
                S_LOAD_INPUTS: begin 
                    for (r = 0; r < PATCH_DIM; r = r + 1) begin
                        for (c = 0; c < PATCH_DIM; c = c + 1) begin
                            patch_pixels_reg[r][c]   <= patch_pixels[r][c];
                            kernel_weights_reg[r][c] <= kernel_weights[r][c];
                        end
                    end
                    bias_val_reg <= bias_val;
                end
                S_MAC_INIT: begin
                    mac_accumulator       <= '0;
                    mac_count             <= 5'd0;
                    product_reg_pipelined <= '0;
                end
                S_MAC_COMPUTE: begin
                    product_reg_pipelined <= current_product_comb;
                    if (mac_count > 0) begin 
                        mac_accumulator <= mac_accumulator + product_reg_pipelined;
                    end
                    mac_count <= mac_count + 1;
                end
                S_ADD_BIAS: begin
                    accumulator_with_bias <= mac_accumulator + product_reg_pipelined + bias_val_reg;
                end
                S_SHIFT_RELU: begin
                    shifted_value <= accumulator_with_bias >>> SHIFT_AMOUNT;
                end
                S_DONE: begin
                    if (shifted_value < 0) begin
                        channel_output_value <= '0;
                    end else begin
                        if (shifted_value > $signed({1'b0, {(OUTPUT_WIDTH-1){1'b1}}})) begin 
                            channel_output_value <= $signed({1'b0,{(OUTPUT_WIDTH-1){1'b1}}});
                        end else begin
                            channel_output_value <= shifted_value[OUTPUT_WIDTH-1:0];
                        end
                    end
                    channel_output_valid <= 1'b1;
                end
                default: ;
            endcase
        end
    end

    always @* begin 
        next_state = current_state;
        case (current_state)
            S_IDLE: begin
                if (start_channel_proc) begin
                    next_state = S_LOAD_INPUTS;
                end
            end
            S_LOAD_INPUTS: begin 
                next_state = S_MAC_INIT;
            end
            S_MAC_INIT: begin
                next_state = S_MAC_COMPUTE;
            end
            S_MAC_COMPUTE: begin
                if (mac_count == NUM_KERNEL_ELEMENTS) begin 
                    next_state = S_ADD_BIAS;
                end else begin
                    next_state = S_MAC_COMPUTE;
                end
            end
            S_ADD_BIAS: begin
                next_state = S_SHIFT_RELU;
            end
            S_SHIFT_RELU: begin
                next_state = S_DONE;
            end
            S_DONE: begin
                next_state = S_IDLE;
            end
            default: begin
                next_state = S_IDLE;
            end
        endcase
    end

    always @* begin 
        logic signed [INPUT_WIDTH:0]  extended_pixel_local;
        logic [$clog2(PATCH_DIM)-1:0] row_idx_local; 
        logic [$clog2(PATCH_DIM)-1:0] col_idx_local; 

        current_product_comb = {PRODUCT_WIDTH{1'b0}}; 
        extended_pixel_local = {(INPUT_WIDTH+1){1'b0}}; 
        row_idx_local        = {$clog2(PATCH_DIM){1'b0}};
        col_idx_local        = {$clog2(PATCH_DIM){1'b0}};

        if (mac_count < NUM_KERNEL_ELEMENTS) begin 
            row_idx_local = mac_count / PATCH_DIM;
            col_idx_local = mac_count % PATCH_DIM;
            
            extended_pixel_local = $signed({1'b0, patch_pixels_reg[row_idx_local][col_idx_local]});
            current_product_comb = extended_pixel_local * $signed(kernel_weights_reg[row_idx_local][col_idx_local]);
        end
    end

endmodule
