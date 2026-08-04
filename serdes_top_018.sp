* =======================================================================
* Full SerDes Physical Layer Top-Level Integration (TX -> Channel -> CTLE -> Sampler)
* Process: CIC / TSMC 0.18um 1.8V CMOS (cic018.l)
* Top-Level Netlist: Interconnects CML Driver + Termination + CTLE + StrongArm Sampler
* Compatible with Synopsys HSPICE 2010.12
* =======================================================================

* 1. Include Process Library
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2 list node

* 2. Global Power & Clock Sources
VDD VDD 0 DC 1.8V
VSS VSS 0 DC 0.0V

* Sampling Clock for RX Sampler (2.5 GHz Clock)
VCLK CLK 0 PULSE(0V 1.8V 0ps 30ps 30ps 170ps 400ps)

* TX Pulse Input (2.5 Gbps Input)
VIN_P IN_P 0 PULSE(0V 1.8V 0ps 50ps 50ps 350ps 800ps)
VIN_N IN_N 0 PULSE(1.8V 0V 0ps 50ps 50ps 350ps 800ps)

* 3. Stage 1: TX CML Driver Circuit
X_TX_DRIVER IN_P IN_N TX_OUT_P TX_OUT_N VDD VSS CML_DRIVER_BLOCK

.subckt CML_DRIVER_BLOCK vin_p vin_n vout_p vout_n vdd vss
M1 vout_n vin_p node_tail vss n_18 W=40u L=0.18u
M2 vout_p vin_n node_tail vss n_18 W=40u L=0.18u
M3 node_tail v_bias vss vss n_18 W=60u L=0.36u M=2
v_bias v_bias 0 DC 0.75V

R1 vdd vout_p 50.0
R2 vdd vout_n 50.0
.ends CML_DRIVER_BLOCK

* 4. Stage 2: Channel & RX Termination (50 Ohm + 100fF ESD)
R_TERM_P TX_OUT_P V_BIAS 50.0
R_TERM_N TX_OUT_N V_BIAS 50.0
V_BIAS   V_BIAS 0 DC 0.9V

C_ESD_P  TX_OUT_P 0 100fF
C_ESD_N  TX_OUT_N 0 100fF

* 5. Stage 3: RX CTLE Equalizer Circuit
X_RX_CTLE TX_OUT_P TX_OUT_N RX_CTLE_P RX_CTLE_N VDD VSS CTLE_BLOCK

.subckt CTLE_BLOCK vin_p vin_n vout_p vout_n vdd vss
M1 vout_n vin_p node_a vss n_18 W=30u L=0.18u
M2 vout_p vin_n node_b vss n_18 W=30u L=0.18u
M3 node_tail v_bias vss vss n_18 W=60u L=0.36u
v_bias v_bias 0 DC 0.80V

Rs1 node_a node_tail 75
Rs2 node_b node_tail 75
Cs  node_a node_b 100fF

RL1 vdd vout_p 650
RL2 vdd vout_n 650
.ends CTLE_BLOCK

* 6. Stage 4: RX StrongArm Latch Sampler Circuit
X_RX_SAMPLER RX_CTLE_P RX_CTLE_N DOUT_P DOUT_N CLK VDD VSS SAMPLER_BLOCK

.subckt SAMPLER_BLOCK vin_p vin_n dout_p dout_n clk vdd vss
M_TAIL node_tail clk vss vss n_18 W=16u L=0.18u

M_IN1 node_l vin_p node_tail vss n_18 W=10u L=0.18u
M_IN2 node_r vin_n node_tail vss n_18 W=10u L=0.18u

M_N1 dout_n dout_p node_l vss n_18 W=8u L=0.18u
M_N2 dout_p dout_n node_r vss n_18 W=8u L=0.18u

M_P1 dout_n dout_p vdd vdd p_18 W=12u L=0.18u
M_P2 dout_p dout_n vdd vdd p_18 W=12u L=0.18u

M_RST1 dout_n clk vdd vdd p_18 W=6u L=0.18u
M_RST2 dout_p clk vdd vdd p_18 W=6u L=0.18u
M_RST3 node_l clk vdd vdd p_18 W=6u L=0.18u
M_RST4 node_r clk vdd vdd p_18 W=6u L=0.18u
.ends SAMPLER_BLOCK

* 7. Transient Analysis & Output Probes (HSPICE 2010.12 Compatible)
.tran 0.1ps 10ns

* Probes for Full Link Waveform Chain
.probe tran v(TX_OUT_P, TX_OUT_N) v(RX_CTLE_P, RX_CTLE_N) v(CLK) v(DOUT_P, DOUT_N) v(DOUT_P) v(DOUT_N)

* Automated Measurements (.meas)
.meas tran v_ctle_max max v(RX_CTLE_P, RX_CTLE_N) from=1ns to=10ns
.meas tran i_total_avg avg i(VDD) from=1ns to=10ns
.meas tran p_total_avg param='1.8 * abs(i_total_avg)'

.end
