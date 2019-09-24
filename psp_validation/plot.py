'''The plot module'''
import os
import h5py
import matplotlib
from tqdm import tqdm


def voltage_traces(traces_files, output_dir):
    """ Plot voltage traces stored in .h5 dump """
    # pylint: disable=too-many-locals
    matplotlib.use('Agg')
    # pylint: disable=import-outside-toplevel
    import matplotlib.pyplot as plt
    matplotlib.rcParams['axes.formatter.useoffset'] = False

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filepath in traces_files:
        pathway = os.path.basename(filepath).split(".", 1)[0]
        pathway_output_dir = os.path.join(output_dir, pathway)
        if not os.path.exists(pathway_output_dir):
            os.makedirs(pathway_output_dir)

        with h5py.File(filepath, 'r') as h5f:
            if len(h5f) != 1:
                raise RuntimeError("Unexpected HDF5 layout")
            root = next(iter(h5f.values()))
            if root.name != "/traces":
                raise RuntimeError("Unexpected HDF5 layout")
            content = h5f.attrs.get('data', 'voltage')
            y_label = {
                'current': 'I [nA]',
                'voltage': 'V [mV]',
            }[content]
            for pair in tqdm(root.values(), total=len(root), desc=pathway):
                title = "a{pre}-a{post}".format(
                    pre=pair.attrs['pre_gid'], post=pair.attrs['post_gid']
                )
                figure = plt.figure()
                ax = figure.gca()
                for k, trial in enumerate(pair['trials']):
                    label = 'trials' if (k == 0) else None  # show 'trials' only once in the legend
                    v_k, t_k = trial
                    ax.plot(t_k, v_k, color='gray', lw=1, ls=':', alpha=0.7, label=label)
                if 'average' in pair:
                    v_avg, t_avg = pair['average']
                    ax.plot(t_avg, v_avg, lw=2, label="average")
                ax.grid()
                ax.set_xlabel('t [ms]')
                ax.set_ylabel(y_label)
                ax.legend()
                ax.set_title(title)
                figure.savefig(os.path.join(pathway_output_dir, title + ".png"), dpi=300)
                plt.close(figure)
