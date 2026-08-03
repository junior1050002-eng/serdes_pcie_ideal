* =======================================================================
* High-Speed SerDes TX CML Output Driver (Optimized Swing & Eye Opening)
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

* 提升 Tail Current 偏置至 0.75V (增加尾電流至約 8mA)
VBIAS V_BIAS 0 DC 0.75V

* 3. Optimized CML Driver Sub-circuit
* 增加 M1, M2 與 M3 尺寸，提高驅動電流，大幅拉開 Eye Height (Vod_p2p > 600mV)
M1 OUT_N IN_P NODE_TAIL VSS N_18 W=40u L=0.18u
M2 OUT_P IN_N NODE_TAIL VSS N_18 W=40u L=0.18u
M3 NODE_TAIL V_BIAS VSS VSS N_18 W=120u L=0.36u

R1 VDD OUT_P 50.0
R2 VDD OUT_N 50.0

* Pad & Package Parasitic Load (C_pad = 100fF)
CPAD1 OUT_P 0 100fF
CPAD2 OUT_N 0 100fF

* 4. Transient Analysis & Probes (2010.12 相容語法)
.tran 1ps 10ns
.probe tran v(OUT_P, OUT_N) v(OUT_P) v(OUT_N)

* 自動測量量化結果 (.meas)
.meas tran vod_max max v(OUT_P, OUT_N) from=1ns to=10ns
.meas tran vod_min min v(OUT_P, OUT_N) from=1ns to=10ns
.meas tran vod_p2p param='vod_max - vod_min'

.end