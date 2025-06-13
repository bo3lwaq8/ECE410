`timescale 1ns/1ps

module conv5x5_wrapper (
    input wire                          clk,
    input wire                          rst_n,
    input wire                          i_start_processing,
    input wire [(25*8)-1:0]             i_patch_pixels_flat,
    input wire [(5*25*16)-1:0]          i_all_weights_flat,
    input wire [(5*16)-1:0]             i_all_biases_flat,
    output logic [(5*16)-1:0]           o_results_flat,
    output logic                        o_processing_done,
    output logic                        o_busy
);

    localparam NUM_CHANNELS          = 5;
    localparam PATCH_DIM             = 5;
    localparam NUM_KERNEL_ELEMENTS   = PATCH_DIM * PATCH_DIM;

    localparam INPUT_WIDTH           = 8;
    localparam WEIGHT_WIDTH          = 16;
    localparam BIAS_WIDTH            = 16;
    localparam OUTPUT_WIDTH          = 16;

    logic                               core_start_channel_proc;
    logic [INPUT_WIDTH-1:0]             core_patch_pixels [0:PATCH_DIM-1][0:PATCH_DIM-1]; 
    logic signed [WEIGHT_WIDTH-1:0]     core_kernel_weights [0:PATCH_DIM-1][0:PATCH_DIM-1];
    logic signed [BIAS_WIDTH-1:0]       core_bias_val;
    logic signed [OUTPUT_WIDTH-1:0]     core_channel_output_value;
    logic                               core_channel_output_valid;
    logic                               core_busy; 

    logic [NUM_KERNEL_ELEMENTS-1:0][INPUT_WIDTH-1:0]   patch_pixels_unpacked;
    logic signed [WEIGHT_WIDTH-1:0] all_weights_unpacked [0:NUM_CHANNELS-1][0:NUM_KERNEL_ELEMENTS-1];
    logic signed [BIAS_WIDTH-1:0]   all_biases_unpacked  [0:NUM_CHANNELS-1];
    logic signed [OUTPUT_WIDTH-1:0] results_reg          [0:NUM_CHANNELS-1];

    typedef enum logic [2:0] {
        S_IDLE_WRAP,
        S_LOAD_INPUTS,
        S_PROC_CHANNEL,
        S_WAIT_CORE_DONE,
        S_DONE_WRAP
    } wrapper_state_t;

    wrapper_state_t current_wstate, next_wstate;
    logic [2:0]     channel_count; 

    conv5x5_core conv_core_inst (
        .clk                    (clk),
        .rst_n                  (rst_n),
        .start_channel_proc     (core_start_channel_proc),
        .patch_pixels           (core_patch_pixels),
        .kernel_weights         (core_kernel_weights),
        .bias_val               (core_bias_val),
        .channel_output_value   (core_channel_output_value),
        .channel_output_valid   (core_channel_output_valid),
        .busy                   (core_busy)
    );

    always @* begin
        integer i, j, ch, k_idx_local; 

        // CORRECTED: Explicit loop initialization for Icarus
        for (k_idx_local = 0; k_idx_local < NUM_KERNEL_ELEMENTS; k_idx_local = k_idx_local + 1) begin
            patch_pixels_unpacked[k_idx_local] = {INPUT_WIDTH{1'b0}};
        end
        for (ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
            for (k_idx_local = 0; k_idx_local < NUM_KERNEL_ELEMENTS; k_idx_local = k_idx_local + 1) begin
                all_weights_unpacked[ch][k_idx_local] = {WEIGHT_WIDTH{1'b0}};
            end
            all_biases_unpacked[ch] = {BIAS_WIDTH{1'b0}};
        end

        for (i = 0; i < PATCH_DIM; i = i + 1) begin
            for (j = 0; j < PATCH_DIM; j = j + 1) begin
                k_idx_local = i * PATCH_DIM + j; 
                patch_pixels_unpacked[k_idx_local] = i_patch_pixels_flat[(k_idx_local*INPUT_WIDTH + INPUT_WIDTH-1) -: INPUT_WIDTH];
            end
        end

        for (ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
            for (i = 0; i < PATCH_DIM; i = i + 1) begin
                for (j = 0; j < PATCH_DIM; j = j + 1) begin
                    k_idx_local = i * PATCH_DIM + j;
                    all_weights_unpacked[ch][k_idx_local] =
                        i_all_weights_flat[ (ch*NUM_KERNEL_ELEMENTS*WEIGHT_WIDTH) + (k_idx_local*WEIGHT_WIDTH) + WEIGHT_WIDTH-1 -: WEIGHT_WIDTH ];
                end
            end
        end

        for (ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
            all_biases_unpacked[ch] =
                i_all_biases_flat[ (ch*BIAS_WIDTH) + BIAS_WIDTH-1 -: BIAS_WIDTH ];
        end
    end

    always @* begin
        integer i, j; 

        // CORRECTED: Explicit loop initialization for Icarus
        for (i = 0; i < PATCH_DIM; i = i + 1) begin
            for (j = 0; j < PATCH_DIM; j = j + 1) begin
                core_patch_pixels[i][j]   = {INPUT_WIDTH{1'b0}};
                core_kernel_weights[i][j] = {WEIGHT_WIDTH{1'b0}};
            end
        end
        core_bias_val       = {BIAS_WIDTH{1'b0}};

        for (i = 0; i < PATCH_DIM; i = i + 1) begin
            for (j = 0; j < PATCH_DIM; j = j + 1) begin
                core_patch_pixels[i][j] = patch_pixels_unpacked[i * PATCH_DIM + j];
            end
        end
        
        if (channel_count < NUM_CHANNELS) begin 
            for (i = 0; i < PATCH_DIM; i = i + 1) begin
                for (j = 0; j < PATCH_DIM; j = j + 1) begin
                    core_kernel_weights[i][j] = all_weights_unpacked[channel_count][i * PATCH_DIM + j];
                end
            end
            core_bias_val = $signed(all_biases_unpacked[channel_count]);
        end
    end

    always @* begin
        integer ch; 
        o_results_flat = {NUM_CHANNELS*OUTPUT_WIDTH{1'b0}}; 
        for (ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
            o_results_flat[(ch * OUTPUT_WIDTH) +: OUTPUT_WIDTH] = results_reg[ch];
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        integer i; 
        if (!rst_n) begin
            current_wstate          <= S_IDLE_WRAP;
            o_busy                  <= 1'b0;
            o_processing_done       <= 1'b0;
            core_start_channel_proc <= 1'b0;
            channel_count           <= 3'd0;
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                results_reg[i] <= {OUTPUT_WIDTH{1'b0}};
            end
        end else begin
            current_wstate <= next_wstate;
            
            o_processing_done       <= 1'b0; 
            core_start_channel_proc <= 1'b0; 

            if (current_wstate == S_IDLE_WRAP && next_wstate != S_IDLE_WRAP) begin 
                o_busy <= 1'b1;
            end else if (current_wstate != S_IDLE_WRAP && next_wstate == S_IDLE_WRAP) begin 
                o_busy <= 1'b0;
            end

            case(current_wstate)
                S_IDLE_WRAP: begin
                    if (i_start_processing) begin 
                        channel_count <= 3'd0;
                        for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                            results_reg[i] <= {OUTPUT_WIDTH{1'b0}};
                        end
                    end
                end
                S_LOAD_INPUTS: begin
                end
                S_PROC_CHANNEL: begin
                    core_start_channel_proc <= 1'b1; 
                end
                S_WAIT_CORE_DONE: begin
                    if (core_channel_output_valid) begin
                        results_reg[channel_count] <= core_channel_output_value;
                        channel_count <= channel_count + 1;
                    end
                end
                S_DONE_WRAP: begin
                    o_processing_done <= 1'b1; 
                end
                default: ;
            endcase
        end
    end

    always @* begin
        next_wstate = current_wstate; 
        case (current_wstate)
            S_IDLE_WRAP: begin
                if (i_start_processing && !o_busy) begin 
                    next_wstate = S_LOAD_INPUTS;
                end
            end
            S_LOAD_INPUTS: begin
                next_wstate = S_PROC_CHANNEL; 
            end
            S_PROC_CHANNEL: begin
                next_wstate = S_WAIT_CORE_DONE;
            end
            S_WAIT_CORE_DONE: begin
                if (core_channel_output_valid) begin
                    if (channel_count == NUM_CHANNELS - 1) begin 
                        next_wstate = S_DONE_WRAP;
                    end else begin
                        next_wstate = S_PROC_CHANNEL; 
                    end
                end
            end
            S_DONE_WRAP: begin
                next_wstate = S_IDLE_WRAP;
            end
            default: begin
                next_wstate = S_IDLE_WRAP;
            end
        endcase
    end

endmodule
