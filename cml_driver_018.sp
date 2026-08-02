* =======================================================================
* High-Speed SerDes TX CML (Current Mode Logic) Output Driver
* Process: CIC / TSMC 0.18um 1.8V CMOS (cic018.l)
* =======================================================================

* 1. Include Process Library
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2 list node

* 2. Power Supply & Biasing
VDD VDD 0 DC 1.8V
VSS VSS 0 DC 0.0V
VCM IN_CM 0 DC 0.9V

* Differential Pulse Input (2.5 Gbps, UI = 400 ps)
VIN_P IN_P IN_CM PULSE(-0.4V 0.4V 0ps 50ps 50ps 350ps 800ps)
VIN_N IN_N IN_CM PULSE(0.4V -0.4V 0ps 50ps 50ps 350ps 800ps)

* Tail Current Bias
VBIAS V_BIAS 0 DC 0.65V

* 3. CML Driver Sub-circuit
* M1, M2: Input Differential Pair
* M3: Tail Current Source (I_tail = 8 mA)
* R1, R2: On-Chip Termination Resistors (50 Ohm Output Matching)
M1 OUT_N IN_P NODE_TAIL VSS N_18 W=20u L=0.18u
M2 OUT_P IN_N NODE_TAIL VSS N_18 W=20u L=0.18u
M3 NODE_TAIL V_BIAS VSS VSS N_18 W=80u L=0.36u

R1 VDD OUT_P 50.0
R2 VDD OUT_N 50.0

* Pad & Package Parasitic Load (C_pad = 100fF)
CPAD1 OUT_P 0 100fF
CPAD2 OUT_N 0 100fF

* 4. Transient Eye Diagram Analysis
.tran 1ps 10ns
.eye_diagram tstart=1ns tstop=10ns period=400ps
.end
