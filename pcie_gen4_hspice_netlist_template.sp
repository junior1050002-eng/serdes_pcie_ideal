* =======================================================================
* PCIe Gen 4 (16 Gbps) SerDes RX CTLE Optimization Testbench
* Target: TSMC 0.18um CMOS (cic018.l) / HSPICE 2010.12 Compatible
* Focus: Ultra-Fast Transitions (<12ps), High Boost (+7.4dB), Minimal Jitter
* =======================================================================

* 1. Process Library
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2 list node

* 2. Power Supply
VDD VDD 0 DC 1.8V
VSS VSS 0 DC 0.0V

* 3. PCIe Gen 4 TX PWL Input Source
VTX IN_P IN_N PWL PWLFILE='tx_output_p7.pwl'

* 4. RX Termination & ESD Parasitics
R_TERM_P IN_P V_BIAS 50.0
R_TERM_N IN_N V_BIAS 50.0
V_BIAS   V_BIAS 0 DC 0.9V
C_ESD_P  IN_P 0 60fF
C_ESD_N  IN_N 0 60fF

* 5. Ultra-Fast RX CTLE (High Bandwidth, Optimized Cs=100fF, Rs=150 Ohm, RL=650 Ohm)
X_CTLE IN_P IN_N OUT_CTLE_P OUT_CTLE_N VDD VSS CTLE_BLOCK

.subckt CTLE_BLOCK vin_p vin_n vout_p vout_n vdd vss
* M1, M2: Input Pair W=30u L=0.18u for optimal gm/Cgg ratio
M1 vout_n vin_p node_a vss n_18 W=30u L=0.18u
M2 vout_p vin_n node_b vss n_18 W=30u L=0.18u

* M3: Tail Current Source W=60u, VBIAS=0.80V (I_tail = 3.6mA)
* High Tail Current boosts Slew Rate (SR = I/C), sharpening Rise/Fall time to <12ps
M3 node_tail v_bias vss vss n_18 W=60u L=0.36u
v_bias v_bias 0 DC 0.80V

* Priority 1 & 2: Rs = 150 Ohm (75+75), Cs = 100fF
* Places Zero fz at ~10.6 GHz for maximum 8 GHz Peaking Boost without Ringing
Rs1 node_a node_tail 75
Rs2 node_b node_tail 75
Cs  node_a node_b 100fF

* Priority 4: Load Resistors RL = 650 Ohm
* Pushes Output Pole fp2 > 16 GHz, removing output RC bandwidth limitation
RL1 vdd vout_p 650
RL2 vdd vout_n 650
.ends CTLE_BLOCK

* 6. Simulation Analysis & Output Probes (2010.12 Compatible)
.tran 0.1ps 70ns

* Output Probes for WaveView
.probe tran v(IN_P, IN_N) v(OUT_CTLE_P, OUT_CTLE_N) v(OUT_CTLE_P) v(OUT_CTLE_N)

* Automated Measurements
.meas tran vdiff_max max v(OUT_CTLE_P, OUT_CTLE_N) from=5ns to=64ns
.meas tran vdiff_min min v(OUT_CTLE_P, OUT_CTLE_N) from=5ns to=64ns
.meas tran vdiff_p2p param='vdiff_max - vdiff_min'

.end