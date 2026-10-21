"""Convert an ECP Executive .plt (binary) file to a PDF plot."""
import re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def read_ecp_plt(path):
    d = open(path, "rb").read()
    assert d.startswith(b"ECP Executive"), "Not an ECP Executive file"
    m = re.search(rb"[ -~]{6,}", d[17:200])      # first printable run after the signature
    title = m.group().decode().strip() if m else ""
    title = ("Cl" + title) if title.startswith("osed") else title   # first 2 bytes are overwritten in the header
    n = 227                                  # sample count (0xE3 in header)
    nch = 3
    start = len(d) - n * nch * 8             # data block sits at end of file
    data = np.frombuffer(d, dtype="<f8", count=n * nch, offset=start).reshape(nch, n)
    return title, data

def main(src, dst):
    title, data = read_ecp_plt(src)
    n = data.shape[1]
    Ts = 1.0 / 113                           # step lasts 113 samples = 1 s -> Ts ~ 8.84 ms
    t = np.arange(n) * Ts
    names = ["Channel 1 (commanded step)", "Channel 2", "Channel 3"]
    fig, axes = plt.subplots(3, 1, figsize=(8.27, 11.69), sharex=True)
    for ax, y, nm in zip(axes, data, names):
        ax.plot(t, y, lw=1.2); ax.set_ylabel("counts"); ax.set_title(nm, fontsize=10, loc="left")
        ax.grid(alpha=.3)
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(f"ECP Executive plot: {title or 'Closed Loop Step'}")
    fig.tight_layout()
    fig.savefig(dst)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        src = input("Enter the path to the .plt file: ").strip().strip("\"'")
        if not src:
            raise SystemExit("No input file provided.")
        src_path = Path(src)
        default_dst = src_path.with_suffix(".pdf")
        dst = input(f"Enter the output PDF path [{default_dst}]: ").strip().strip("\"'")
        if not dst:
            dst = str(default_dst)
        main(src_path, dst)
        print(f"PDF created: {dst}")
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit("Usage: python ecp_plt_to_pdf.py input.plt output.pdf")

