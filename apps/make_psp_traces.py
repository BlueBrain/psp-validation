#!/usr/bin/env python

import logging

from bluepy.utils import gid2str


LOGGER = logging.getLogger(__name__)


def get_parser():
    '''Set up the arguments parser'''
    import argparse
    parser = argparse.ArgumentParser(description='PSP trace maker',
            epilog='./make_psp_traces job_config.json --verbose --log=psp.log')
    parser.add_argument('config', help='json configuration file')
    parser.add_argument('-v', '--verbose', action='count', dest='verbose',
                        default=0, help='-v for INFO, -vv for DEBUG')
    parser.add_argument('-l', '--log', dest='log_file',
                        default="", help="File to log to")
    return parser


def setup_logging(args):
    '''set the level of verbosity to INFO or DEBUG'''
    if args.verbose > 0:  # turns on logging to console
        if args.verbose > 2:
            sys.exit("can't be more verbose than -vv")
        logging.basicConfig(level=(logging.WARNING,
                                   logging.INFO,
                                   logging.DEBUG)[args.verbose],
                            filename = args.log_file)


def get_traces(sim_config, pre_gid, post_gid, protocol):
    from psp_validation.psp import run_pair_trace_simulations

    blue_config = sim_config.blue_config

    if protocol.holding_V is None:
        hold_I = None
    else:
        from psp_validation.holding_current import holding_current
        LOGGER.info("Calculating %s holding current", gid2str(post_gid))
        hold_I, _ = holding_current(protocol.holding_V, post_gid, blue_config, xtol=0.0001)

    LOGGER.info("Running simulation(s) for %s -> %s pair", gid2str(pre_gid), gid2str(post_gid))
    return run_pair_trace_simulations(
        blue_config=blue_config,
        pre_gid=pre_gid,
        post_gid=post_gid,
        hold_I=hold_I,
        hold_V=protocol.holding_V,
        t_stim=protocol.t_stim,
        t_stop=protocol.t_stop,
        g_factor=protocol.g_factor,
        record_dt=protocol.record_dt,
        post_ttx=protocol.post_ttx,
        v_clamp=protocol.clamp_V,
        spikes=None,
        rndm_seed=sim_config.rndm_seed,
        repetitions=sim_config.n_repetitions,
        use_multiprocessing=sim_config.multiprocessing
    )


def main(args):
    print args
    import os
    import h5py
    import numpy as np
    import bluepy
    from psp_validation import pathways
    from psp_validation import configutils as cu
    from psp_validation import persistencyutils as pu
    import json
    import shutil


    configfile = args.config

    setup_logging(args)

    amplitudes = []

    sim_config = cu.json2simconfig(open(configfile))

    pways = sim_config.pathways

    protocols = [cu.json2protocol(open(p)) for p in sim_config.protocols]

    circuit = bluepy.Circuit(sim_config.blue_config).v2

    LOGGER.info('Starting job with configuration file %s', configfile)
    out_dir = pu.mkjobdir(sim_config.output_dir)
    LOGGER.info('Output will be written to %s', out_dir)
    out_filename = os.path.join(out_dir, 'psp_traces.hdf5')
    #hfile = h5py.File(out_filename, 'w')
    shutil.copyfile(configfile, os.path.join(out_dir, 'jobconfig.json'))

    for pathway, protocol in zip(pways, protocols) :
        title = pathway['title']
        LOGGER.info('Processing PATHWAY=%s, PROTOCOL=%s', title, str(protocol))
        pairs = pathways.get_pairs(
            circuit, sim_config.n_pairs,
            query=pathway['query'],
            constraints=pathway.get('constraints')
        )
        psp_traces = [
            get_traces(sim_config, pre_gid, post_gid, protocol)
            for pre_gid, post_gid in pairs
        ]

        hfile = h5py.File(out_filename, 'w')
        pu.dump_raw_traces_to_HDF5(hfile, title, psp_traces)

        hfile.close()

    #hfile.close()


if __name__ == "__main__" :

    PARSER = get_parser()
    args = PARSER.parse_args()
    main(args)
