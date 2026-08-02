* =======================================================================
* High-Speed SerDes RX CTLE (Continuous-Time Linear Equalizer)
* Process: CIC / TSMC 0.18um 1.8V CMOS (cic018.l)
* Topology: Source-Degenerated Differential Pair
* =======================================================================

* 1. Include Process Library
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2 list node

* 2. Power Supply & Biasing
VDD VDD 0 DC 1.8V
VSS VSS 0 DC 0.0V
VCM IN_CM 0 DC 0.9V

* Common-Mode Bias + Differential AC Input
VIN_P IN_P IN_CM DC 0.0V AC 0.5V 0deg
VIN_N IN_N IN_CM DC 0.0V AC 0.5V 180deg

* Tail Current Bias Voltage
VBIAS V_BIAS 0 DC 0.65V

* 3. CTLE Sub-circuit Definition
M1 OUT_N IN_P NODE_A VSS N_18 W=10u L=0.18u
M2 OUT_P IN_N NODE_B VSS N_18 W=10u L=0.18u
M3 NODE_TAIL V_BIAS VSS VSS N_18 W=20u L=0.36u

* Source Degeneration RC Network (RS & CS)
RS1 NODE_A NODE_TAIL 250
RS2 NODE_B NODE_TAIL 250
CS  NODE_A NODE_B 350fF

* Load Resistors (RL)
RL1 VDD OUT_P 1.2k
RL2 VDD OUT_N 1.2k

* 4. AC Frequency Analysis (1MHz to 10GHz)
.ac dec 20 1Meg 10Gig

* Measure DC Gain and Peaking Boost at Nyquist Frequency (1.25 GHz)
.meas ac dc_gain_db find vdb(OUT_P, OUT_N) at=1Meg
.meas ac nyq_gain_db find vdb(OUT_P, OUT_N) at=1.25Gig
.meas ac peak_boost_db param='nyq_gain_db - dc_gain_db'

.end
