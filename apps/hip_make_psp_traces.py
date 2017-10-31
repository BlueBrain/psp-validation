#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PSP validation: finds pairs for a given pathway (see config files) runs multiple simulations with BGLibPy and saves traces
BEWARE! The latest BGLibPy (09.2017) doesn't reload cell templates if it was loaded previously - in some releases (eg. hippocampus 2016.12) all the cell templates had the same name - which will cause serious issues!
pairFilter() factored out - overall pair selection process replaced by Giuseppe's bbuutils.targetselector (could be better...)
Eilif's script modified by Andras for the hippocampal circuit (12.2016)
"""

import sys
if '.' not in sys.path :
    sys.path.append('.')


def get_parser():
    '''Set up the arguments parser'''
    import argparse
    parser = argparse.ArgumentParser(description='PSP trace maker',
            epilog='./hip_make_psp_traces job_config.json --verbose --log=psp.log')
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

    import os
    import h5py
    import numpy as np
    from psp_validation import hip_pathways  as pathways # modified here!
    from psp_validation import hip_simpathways as sim  # modified here
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

    LOGGER.info('Starting job with configuration file %s', configfile)
    out_dir = pu.mkjobdir(sim_config.output_dir)
    LOGGER.info('Output will be written to %s', out_dir)
    out_filename = os.path.join(out_dir, 'psp_traces.hdf5')
    shutil.copyfile(configfile, os.path.join(out_dir, 'jobconfig.json'))

    hfile = h5py.File(out_filename, 'w') 
    for pathway, protocol in zip(pways, protocols) :
        LOGGER.info('Processing PATHWAY=%s, PROTOCOL=%s', pathway, str(protocol))
        pway = pathways.get_pathway(pathway)
        eps = sim.PathwayEPhys(pway, protocol, sim_config)
        print eps
        psp_traces = eps.traces()
        # write traces to hdf5 file
        pu.dump_raw_traces_to_HDF5(hfile, pathway, psp_traces)

    hfile.close()


if __name__ == "__main__" :

    PARSER = get_parser()
    args = PARSER.parse_args()
    main(args)
