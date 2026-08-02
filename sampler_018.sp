* =======================================================================
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
