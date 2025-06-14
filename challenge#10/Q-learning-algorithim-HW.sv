module q_update_datapath #(
    parameter DATA_WIDTH = 32,
    parameter NUM_ACTIONS = 4
) (
    input  logic signed [DATA_WIDTH-1:0] q_current,
    input  logic signed [DATA_WIDTH-1:0] reward,
    input  logic signed [DATA_WIDTH-1:0] q_next_max,
    input  logic signed [DATA_WIDTH-1:0] learning_rate,
    input  logic signed [DATA_WIDTH-1:0] gamma,
    output logic signed [DATA_WIDTH-1:0] q_new
);

    logic signed [DATA_WIDTH-1:0] term1, term2, term3;

    // term1 = gamma * max_q_next
    // Note: For actual hardware, this would likely be implemented with fixed-point
    // arithmetic and potentially shifters for powers of two.
    always_comb begin
        term1 = gamma * q_next_max;
    end

    // term2 = reward + term1
    always_comb begin
        term2 = reward + term1;
    end

    // term3 = term2 - q_current
    always_comb begin
        term3 = term2 - q_current;
    end

    // q_new = q_current + learning_rate * term3
    always_comb begin
        q_new = q_current + (learning_rate * term3);
    end

endmodule