* =======================================================================
* PCIe Gen 4 (16 Gbps) SerDes Physical Layer Circuit Testbench Template
* Technology: TSMC / Generic CMOS Process
* =======================================================================

* 1. Include Semiconductor Process PDK (.lib)
.lib 'tsmc28nm.lib' tt
.option post=2 probe=1 ingold=2

* 2. Global Power & Clock Sources
VDD VDD 0 DC 1.0V
VSS VSS 0 DC 0.0V

* 3. Import PWL Waveform Exported from Python (tx_output_p7.pwl)
V_TX_IN IN_P IN_N PWL file='tx_output_p7.pwl'

* 4. RX On-Chip Termination & ESD Parasitics (200fF ESD + 50 Ohm Termination)
R_TERM_P IN_P V_BIAS 50.0
R_TERM_N IN_N V_BIAS 50.0
V_BIAS   V_BIAS 0 DC 0.5V
C_ESD_P  IN_P 0 200fF
C_ESD_N  IN_N 0 200fF

* 5. RX CTLE (Source-Degenerated Differential Pair Topology)
* CTLE Transistors: M1, M2 (Input Pair)
* Source Degeneration: Rs = 200 Ohm, Cs = 150 fF (Achieves +12dB Boost @ 8GHz)
* Load Resistors: R_L1, R_L2 = 1k Ohm
X_CTLE IN_P IN_N OUT_CTLE_P OUT_CTLE_N VDD VSS CTLE_BLOCK

.subckt CTLE_BLOCK vin_p vin_n vout_p vout_n vdd vss
M1 vout_n vin_p node_a vss nch W=10u L=0.03u
M2 vout_p vin_n node_b vss nch W=10u L=0.03u
Rs node_a node_b 200
Cs node_a node_b 150fF
RL1 vdd vout_p 1k
RL2 vdd vout_n 1k
Iss node_a vss DC 1mA
.ends CTLE_BLOCK

* 6. Simulation Analysis Commands
* AC Frequency Sweep Analysis (Check CTLE +12dB Boost @ 8GHz)
.ac dec 20 100MHz 20GHz

* Transient Eye Diagram Analysis
.tran 0.1ps 125ns

* Eye Diagram Generation Syntax
.eye_diagram tstart=10ns tstop=125ns period=62.5ps
.end
