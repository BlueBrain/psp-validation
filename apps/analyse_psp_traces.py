#!/usr/bin/env python

import os
import logging

import h5py
import numpy as np

from psp_validation import psp
from psp_validation.config import load_config


LOGGER = logging.getLogger(__name__)


def main(args):
    logging.basicConfig(level=logging.WARNING)
    LOGGER.setLevel(logging.INFO)

    if args.output_dir is None:
        output_dir = args.traces_dir
    else:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

    for input_path in args.input:
        title, config = load_config(input_path)

        traces_path = os.path.join(args.traces_dir, title + "_traces.h5")
        if not os.path.exists(traces_path):
            LOGGER.warn("No PSP traces found for %s", basename)
            continue

        t_stim = config['protocol']['t_stim']
        t_start = t_stim - 10.
        spike_filter = psp.default_spike_filter(t_start)

        output_path = os.path.join(output_dir, title + "_amplitudes.csv")
        LOGGER.info("%s -> %s", traces_path, output_path)

        amplitudes = []
        with h5py.File(traces_path, 'r') as h5f:
            assert len(h5f['/pathways']) == 1
            data = h5f['/pathways'].values()[0]['pairs']
            for p in data.itervalues():
                pre_gid = p.attrs['gid_pre']
                syn_type = psp.synapse_type(args.circuit, pre_gid)
                v_mean, t, vts, _ = psp.mean_pair_voltage_from_traces(p, spike_filter)
                ampl = psp.get_peak_amplitude(t, v_mean, t_start, t_stim, syn_type)
                amplitudes.append(ampl)
        np.savetxt(output_path, amplitudes)


if __name__ == "__main__" :
    import argparse
    parser = argparse.ArgumentParser(description="Extract PSP amplitudes")
    parser.add_argument(
        "-c", "--circuit",
        required=True,
        help="Path to BlueConfig"
    )
    parser.add_argument(
        "-t", "--traces-dir",
        required=True,
        help="Path folder with PSP traces"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Path to output folder (if not defined, same as traces folder)"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="YAML job config(s)"
    )
    main(parser.parse_args())