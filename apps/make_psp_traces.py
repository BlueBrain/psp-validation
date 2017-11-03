#!/usr/bin/env python

import os
import yaml
import logging

import h5py
import numpy as np

import bluepy

from psp_validation.pathways import get_pairs
from psp_validation.persistencyutils import dump_raw_traces_to_HDF5


LOGGER = logging.getLogger(__name__)


def get_traces(blue_config, pre_gid, post_gid, protocol, n_repetitions, seed):
    from psp_validation.psp import run_pair_trace_simulations

    hold_V = protocol['hold_V']
    if hold_V is None:
        hold_I = None
    else:
        from psp_validation.holding_current import holding_current
        LOGGER.info("Calculating a%d holding current", post_gid)
        hold_I, _ = holding_current(hold_V, post_gid, blue_config, xtol=0.0001)

    LOGGER.info("Running simulation(s) for a%d -> a%d pair (base_seed=%d)", pre_gid, post_gid, seed)
    return run_pair_trace_simulations(
        blue_config=blue_config,
        pre_gid=pre_gid,
        post_gid=post_gid,
        hold_I=hold_I,
        hold_V=hold_V,
        t_stim=protocol['t_stim'],
        t_stop=protocol['t_stop'],
        g_factor=1.0,
        record_dt=protocol['record_dt'],
        post_ttx=protocol['post_ttx'],
        v_clamp=protocol['v_clamp'],
        spikes=None,
        repetitions=n_repetitions,
        rndm_seed=seed,
        use_multiprocessing=True
    )


def load_yaml(filepath):
    with open(filepath, 'r') as f:
        return yaml.load(f)


def main(args):
    logging.basicConfig(level=logging.WARNING)
    LOGGER.setLevel({
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG
    }[args.verbose])

    if args.seed is None:
        seed = np.random.randint(1e9)
    else:
        seed = args.seed

    np.random.seed(seed)

    circuit = bluepy.Circuit(args.circuit).v2

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    for input_path in args.input:
        basename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(args.output_dir, basename + ".h5")
        LOGGER.info("%s -> %s", input_path, output_path)

        job_config = load_yaml(input_path)

        pathway = job_config['pathway']
        if isinstance(pathway, list):
            for item in pathway:
                assert isinstance(item, list) and len(item) == 2
            pairs = pathway
        else:
            LOGGER.info("Querying pathway pairs...")
            pairs = get_pairs(circuit, **pathway)

        protocol = job_config['protocol']
        n_repetitions = job_config['n_repetitions']

        LOGGER.info("Obtaining PSP traces...")
        psp_traces = [
            get_traces(args.circuit, pre_gid, post_gid, protocol, n_repetitions, seed=seed)
            for pre_gid, post_gid in pairs
        ]

        with h5py.File(output_path, 'w') as hfile:
            dump_raw_traces_to_HDF5(hfile, basename, psp_traces)


if __name__ == "__main__" :
    import argparse
    parser = argparse.ArgumentParser(description="PSP trace maker")
    parser.add_argument(
        "-c", "--circuit",
        required=True,
        help="Path to BlueConfig"
    )
    parser.add_argument(
        "-o", "--output-dir",
        required=True,
        help="Path to output folder"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Pseudo-random generator seed"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="-v for INFO, -vv for DEBUG"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="YAML job config(s)"
    )
    main(parser.parse_args())
