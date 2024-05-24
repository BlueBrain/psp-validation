"""The plot module."""

import h5py
import matplotlib as mpl
from tqdm import tqdm

mpl.use("Agg")
import matplotlib.pyplot as plt


def voltage_traces(traces_files, output_dir):
    """Plot voltage traces stored in .h5 dump"""
    mpl.rcParams["axes.formatter.useoffset"] = False

    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in traces_files:
        pathway = filepath.stem
        pathway_output_dir = output_dir / pathway
        pathway_output_dir.mkdir(exist_ok=True)

        with h5py.File(filepath, "r") as h5f:
            if len(h5f) != 1:
                raise RuntimeError("Unexpected HDF5 layout")
            root = next(iter(h5f.values()))
            if root.name != "/traces":
                raise RuntimeError("Unexpected HDF5 layout")
            content = h5f.attrs.get("data", "voltage")
            y_label = {
                "current": "I [nA]",
                "voltage": "V [mV]",
            }[content]
            for pair in tqdm(root.values(), total=len(root), desc=pathway):
                title = (
                    f"{pair.attrs['pre_population']}-{pair.attrs['pre_id']}"
                    f"-{pair.attrs['post_population']}-{pair.attrs['post_id']}"
                )
                figure = plt.figure()
                ax = figure.gca()
                for k, trial in enumerate(pair["trials"]):
                    label = "trials" if (k == 0) else None  # show 'trials' only once in the legend
                    v_k, t_k = trial
                    ax.plot(t_k, v_k, color="gray", lw=1, ls=":", alpha=0.7, label=label)
                if "average" in pair:
                    v_avg, t_avg = pair["average"]
                    ax.plot(t_avg, v_avg, lw=2, label="average")
                ax.grid()
                ax.set_xlabel("t [ms]")
                ax.set_ylabel(y_label)
                ax.legend()
                ax.set_title(title)
                figure.savefig(pathway_output_dir / f"{title}.png", dpi=300)
                plt.close(figure)
