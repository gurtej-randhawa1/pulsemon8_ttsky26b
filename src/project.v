/*
 * Copyright (c) 2026 Gurtejbir Randhawa
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_gurtej_randhawa1_pulsemon8(
  input  wire [7:0] ui_in,    // Dedicated inputs
  output wire [7:0] uo_out,   // Dedicated outputs
  input  wire [7:0] uio_in,   // Bidirectional IO input path
  output wire [7:0] uio_out,  // Bidirectional IO output path
  output wire [7:0] uio_oe,   // Bidirectional IO output enable, active high
  input  wire       ena,      // Design enable
  input  wire       clk,      // Clock
  input  wire       rst_n     // Active-low reset
);

  // ---------------------------------------------------------------------------
  // Pin mapping
  // ---------------------------------------------------------------------------

  // uio[3:0] are status outputs.
  // uio[7:4] are user control inputs.
  assign uio_oe = 8'b0000_1111;

  wire [7:0] compare_value   = ui_in[7:0];
  wire       signal          = uio_in[4];
  wire       enable          = uio_in[5];
  wire       clear           = uio_in[6];
  wire       freeze_on_match = uio_in[7];

  // ---------------------------------------------------------------------------
  // Internal state
  // ---------------------------------------------------------------------------

  reg [7:0] count;
  reg       prev_signal;
  reg       overflow;
  reg       freeze_status;

  // ---------------------------------------------------------------------------
  // Combinational status logic
  // ---------------------------------------------------------------------------

  wire edge_detect  = signal && !prev_signal;
  wire match_status = (count == compare_value);

  // ---------------------------------------------------------------------------
  // Sequential counter/control logic
  // ---------------------------------------------------------------------------

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count         <= 8'b0;
      prev_signal   <= 1'b0;
      overflow      <= 1'b0;
      freeze_status <= 1'b0;
    end else begin
      prev_signal <= signal;

      if (clear) begin
        count         <= 8'b0;
        overflow      <= 1'b0;
        freeze_status <= 1'b0;
      end else if (!freeze_status && enable && edge_detect) begin
        if (count == 8'hFF) begin
          overflow <= 1'b1;
        end

        count <= count + 1'b1;

        if (freeze_on_match && ((count + 1'b1) == compare_value)) begin
          freeze_status <= 1'b1;
        end
      end
    end
  end

  // ---------------------------------------------------------------------------
  // Output assignments
  // ---------------------------------------------------------------------------

  assign uo_out = count;

  assign uio_out[0]   = edge_detect;
  assign uio_out[1]   = overflow;
  assign uio_out[2]   = match_status;
  assign uio_out[3]   = freeze_status;
  assign uio_out[7:4] = 4'b0000;

  // Mark ena as intentionally unused.
  wire _unused = &{ena, 1'b0};

endmodule
