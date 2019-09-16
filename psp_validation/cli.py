#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PSP analysis toolkit.

 * `psp run`     Run pair simulations for given pathway(s)
 * `psp summary` Collect `psp run` summary output
 * `psp plot`    Plot voltage / current traces obtained with `psp run`
"""

from __future__ import print_function

import os
import logging

import click
import h5py

from psp_validation import get_logger, setup_logging
from psp_validation.utils import load_yaml
from psp_validation.version import VERSION

LOGGER = get_logger()


@click.group()
@click.version_option(version=VERSION)
@click.option("-v", "--verbose", count=True, help="-v for INFO, -vv for DEBUG")
def cli(verbose=0):
    """ PSP analysis tool """
    level = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG
    }[verbose]
    setup_logging(level)


@cli.command()
@click.argument("pathway_files", nargs=-1, required=True)
@click.option("-c", "--blueconfig", required=True, help="Path to BlueConfig")
@click.option("-t", "--targets", required=True, help="Path to neuron groups definitions (YAML)")
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option(
    "-n", "--num-pairs", type=int, required=True, help="Sample NUM_PAIRS pairs from each pathway"
)
@click.option(
    "-r", "--num-trials", type=int, required=True, help="Run NUM_TRIALS simulations for each pair"
)
@click.option(
    "-m", "--clamp", type=click.Choice(['current', 'voltage']),
    help="Clamp type used", default='current', show_default=True
)
@click.option("--dump-traces", is_flag=True, help="Dump PSP traces", show_default=True)
@click.option("--dump-amplitudes", is_flag=True, help="Dump PSP amplitudes", show_default=True)
@click.option("--seed", type=int, help="Pseudo-random generator seed", default=0, show_default=True)
@click.option(
    "-j", "--jobs", type=int,
    help=(
        "Number of trials to run in parallel"
        "(if not specified, trials are run sequentially; "
        "setting to 0 would use all available CPUs)"
    )
)
def run(
    pathway_files, blueconfig, targets, output_dir, num_pairs, num_trials,
    clamp='current', dump_traces=False, dump_amplitudes=False, seed=None, jobs=None
):
    """ Obtain PSP amplitudes; derive scaling factors """
    # pylint: disable=too-many-arguments
    from psp_validation import psp

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    psp.run(pathway_files, blueconfig, targets, output_dir, num_pairs, num_trials,
            clamp, dump_traces, dump_amplitudes, seed, jobs)


@cli.command()
@click.argument("summary_files", nargs=-1)
@click.option("-s", "--style", type=click.Choice(['default', 'jira']), help="Table style")
@click.option("--with-scaling", is_flag=True, help="Include 'scaling' column")
def summary(summary_files, with_scaling=False, style='default'):
    """ Print table with `psp run` output summary """
    def _format_value(value):
        if value is None:
            return "N/A"
        else:
            return "%.6g" % value

    def _format_value_mean_std(value):
        if value is None:
            return "N/A"
        else:
            return "%.6g±%.6g" % (value['mean'], value['std'])

    def _add_borders(values):
        return [''] + values + ['']

    headers = ['pathway', 'reference', 'model']
    if with_scaling:
        headers.append('scaling')
    if style == 'jira':
        print(*_add_borders(headers), sep="||")
    else:
        print(*headers, sep="\t")

    for filepath in summary_files:
        data = load_yaml(filepath)
        row = [
            data['pathway'],
            _format_value_mean_std(data.get('reference')),
            _format_value_mean_std(data.get('model'))
        ]
        if with_scaling:
            row.append(
                _format_value(data.get('scaling'))
            )
        if style == 'jira':
            print(*_add_borders(row), sep="|")
        else:
            print(*row, sep="\t")


@cli.command()
@click.argument("traces_files", nargs=-1)
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
def plot(traces_files, output_dir):
    """ Plot voltage traces stored in .h5 dump """
    # pylint: disable=too-many-locals
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['axes.formatter.useoffset'] = False
    import matplotlib.pyplot as plt
    from tqdm import tqdm

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
            root = next(h5f.itervalues())
            if root.name != "/traces":
                raise RuntimeError("Unexpected HDF5 layout")
            content = h5f.attrs.get('data', 'voltage')
            y_label = {
                'current': 'I [nA]',
                'voltage': 'V [mV]',
            }[content]
            for pair in tqdm(root.itervalues(), total=len(root), desc=pathway):
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


if __name__ == "__main__":
    cli()
