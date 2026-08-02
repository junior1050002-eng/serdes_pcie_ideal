import os

# TSMC 0.18um (cic018.l) 1.8V CMOS SerDes 子電路網表建立腳本
files = {
    "ctle_018.sp": '''* =======================================================================
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
.ac dec 20 1MHz 10GHz

* Measure DC Gain and Peaking Boost at Nyquist Frequency (1.25 GHz)
.meas ac dc_gain_db val='vdb(OUT_P, OUT_N)' at=1MHz
.meas ac nyq_gain_db val='vdb(OUT_P, OUT_N)' at=1.25GHz
.meas ac peak_boost_db param='nyq_gain_db - dc_gain_db'

.end
''',

    "cml_driver_018.sp": '''* =======================================================================
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
''',

    "sampler_018.sp": '''* =======================================================================
* High-Speed SerDes RX StrongArm Latch Comparator / Sampler
* Process: CIC / TSMC 0.18um 1.8V CMOS (cic018.l)
* =======================================================================

* 1. Include Process Library
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2 list node

* 2. Power Supply & Clock
VDD VDD 0 DC 1.8V
VSS VSS 0 DC 0.0V

* Sampling Clock (2.5 GHz Clock)
VCLK CLK 0 PULSE(0V 1.8V 0ps 30ps 30ps 170ps 400ps)

* Differential Small Signal Input
VIN_P IN_P 0 DC 0.92V
VIN_N IN_N 0 DC 0.88V

* 3. StrongArm Latch Circuit Topology
* Tail Switch
M_TAIL NODE_TAIL CLK VSS VSS N_18 W=16u L=0.18u

* Differential Input Pair
M_IN1 NODE_L IN_P NODE_TAIL VSS N_18 W=10u L=0.18u
M_IN2 NODE_R IN_N NODE_TAIL VSS N_18 W=10u L=0.18u

* Cross-Coupled Inverter Pair (Latching Stage)
M_N1 OUT_N OUT_P NODE_L VSS N_18 W=8u L=0.18u
M_N2 OUT_P OUT_N NODE_R VSS N_18 W=8u L=0.18u

M_P1 OUT_N OUT_P VDD VDD P_18 W=12u L=0.18u
M_P2 OUT_P OUT_N VDD VDD P_18 W=12u L=0.18u

* Precharge Switches (Reset Phase)
M_RST1 OUT_N CLK VDD VDD P_18 W=6u L=0.18u
M_RST2 OUT_P CLK VDD VDD P_18 W=6u L=0.18u
M_RST3 NODE_L CLK VDD VDD P_18 W=6u L=0.18u
M_RST4 NODE_R CLK VDD VDD P_18 W=6u L=0.18u

* 4. Transient Analysis
.tran 1ps 4ns
.end
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("[+] TSMC 0.18um (cic018.l) 三大子電路網表範本建立完成！")