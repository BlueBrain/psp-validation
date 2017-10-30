#!/usr/bin/env python

import sys
if '.' not in sys.path :
    sys.path.append('.')


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
    import logging
    if args.verbose > 0:  # turns on logging to console
        if args.verbose > 2:
            sys.exit("can't be more verbose than -vv")
        logging.basicConfig(level=(logging.WARNING,
                                   logging.INFO,
                                   logging.DEBUG)[args.verbose],
                            filename = args.log_file)
    return logging.getLogger(__name__)


def main(args):
    print args
    import os
    import h5py
    import numpy as np
    import bluepy
    from psp_validation import pathways
    from psp_validation import simpathways as sim
    from psp_validation import configutils as cu
    from psp_validation import persistencyutils as pu
    import json
    import shutil


    configfile = args.config

    LOGGER = setup_logging(args)

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
        LOGGER.info('Selected pairs: %s', str(pairs))
        eps = sim.PathwayEPhys(pairs, protocol, sim_config, pair_selection=None)
        psp_traces = eps.traces()
        hfile = h5py.File(out_filename, 'w')
        pu.dump_raw_traces_to_HDF5(hfile, title, psp_traces)

        hfile.close()

    #hfile.close()


if __name__ == "__main__" :

    PARSER = get_parser()
    args = PARSER.parse_args()
    main(args)
