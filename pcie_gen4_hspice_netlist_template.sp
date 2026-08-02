* =======================================================================
* PCIe Gen 4 SerDes Testbench (HSPICE 2010.12 Compatible)
* =======================================================================

* 1. Include Library (請確認 cic018.l 與此檔在同資料夾)
.lib 'cic018.l' TT
.option post=2 probe=1 ingold=2

* 2. Power
VDD VDD 0 DC 1.0V
VSS VSS 0 DC 0.0V

* 3. TX Input (使用你測試成功的 PWLFILE 語法)
* 注意：若仍報錯，請嘗試 VTX IN_P IN_N PWL (FILE='tx_output_p7.pwl')
VTX IN_P IN_N PWL PWLFILE='tx_output_p7.pwl'

* 4. RX Termination
R_TERM_P IN_P V_BIAS 50.0
R_TERM_N IN_N V_BIAS 50.0
V_BIAS   V_BIAS 0 DC 0.5V
C_ESD_P  IN_P 0 200fF
C_ESD_N  IN_N 0 200fF

* 5. RX CTLE
X_CTLE IN_P IN_N OUT_CTLE_P OUT_CTLE_N VDD VSS CTLE_BLOCK

.subckt CTLE_BLOCK vin_p vin_n vout_p vout_n vdd vss
* 將 nch 改為 n_18 (這是 cic018 常用名稱，若不對請查閱 .l 檔)
* 將 L 改為 0.18u (0.18um 製程不能跑 0.03u)
M1 vout_n vin_p node_a vss n_18 W=10u L=0.18u
M2 vout_p vin_n node_b vss n_18 W=10u L=0.18u
Rs node_a node_b 200
Cs node_a node_b 150fF
RL1 vdd vout_p 1k
RL2 vdd vout_n 1k
Iss node_a vss DC 1mA
.ends CTLE_BLOCK

* 6. Analysis
.ac dec 20 100MHz 20GHz
.tran 1ps 125ns

* 2010.12 不支援 .eye_diagram，改用 .probe 輸出差動訊號
.probe tran v(OUT_CTLE_P, OUT_CTLE_N)
.end