"""
HSPICE Stimulus Generator
Generate differential PRBS7 TX input
for HSPICE E-2010.12

Output:
stimulus.inc
"""

import numpy as np
from pcie_gen4_serdes.tx import TXTop


def export_stimulus(time_vec, tx_waveform):

    vcm = 0.9

    tx_p = vcm + tx_waveform / 2
    tx_n = vcm - tx_waveform / 2


    with open("stimulus.inc", "w") as f:

        f.write("* =====================================\n")
        f.write("* Python Generated PCIe Gen4 PRBS7 TX\n")
        f.write("* Differential TX Input\n")
        f.write("* =====================================\n\n")


        # TX positive

        f.write("VIN_P IN_P 0 PWL(\n")

        for t, v in zip(time_vec, tx_p):
            f.write(f"+ {t:.6e} {v:.6f}\n")

        f.write(")\n\n")


        # TX negative

        f.write("VIN_N IN_N 0 PWL(\n")

        for t, v in zip(time_vec, tx_n):
            f.write(f"+ {t:.6e} {v:.6f}\n")

        f.write(")\n")


    print("[+] Generated stimulus.inc")



def main():

    tx = TXTop(
        prbs_order=7,
        preset_name="P7",
        enable_non_idealities=True
    )


    time_vec, tx_waveform, bits, _ = tx.run(
        num_bits=3200
    )
    np.save("tx_bits.npy", bits)


    export_stimulus(
        time_vec,
        tx_waveform
    )



if __name__ == "__main__":
    main()