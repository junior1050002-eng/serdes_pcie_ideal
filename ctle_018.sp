* =======================================================================
* High-Speed SerDes RX CTLE AC Frequency Response Optimization
* Process: CIC / TSMC 0.18um 1.8V CMOS (cic018.l)
* Target: PCIe Gen 4 (16 Gbps, Nyquist = 8 GHz)
* =======================================================================

* 1. Process Library
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
VBIAS V_BIAS 0 DC 0.80V

* 3. CTLE Sub-circuit
M1 OUT_N IN_P NODE_A VSS N_18 W=30u L=0.18u
M2 OUT_P IN_N NODE_B VSS N_18 W=30u L=0.18u
M3 NODE_TAIL V_BIAS VSS VSS N_18 W=60u L=0.36u

RS1 NODE_A NODE_TAIL 75
RS2 NODE_B NODE_TAIL 75
CS  NODE_A NODE_B 100fF

RL1 VDD OUT_P 2000
RL2 VDD OUT_N 2000

* 4. AC Frequency Analysis (1MHz to 30GHz)
.ac dec 20 1Meg 30Gig

* Output Probes
.probe ac vdb(OUT_P, OUT_N) vp(OUT_P, OUT_N)

* Automated Measurements
.meas ac dc_gain_db find vdb(OUT_P, OUT_N) at=1Meg
.meas ac nyq_gain_db find vdb(OUT_P, OUT_N) at=8Gig
.meas ac peak_boost_db param='nyq_gain_db - dc_gain_db'

.end