"""
Check the amplitude of the compound *E*PSP; works only with excitatory
synapses at this time. However, no checks are done to see if you actually
specified an excitatory synapse. Be carefull.
Minis are not used because they provide too much noise.
No current injection other than the current to achieve the holding potential
are included. (no HypAmp for instance)
"""
from functools import partial

import attr
from bluepy.v2 import Circuit
import numpy as np

from psp_validation import get_logger, PSPError
from psp_validation.pathways import Pathway
from psp_validation.simulation import run_pair_simulation_suite
from psp_validation.utils import load_yaml

LOGGER = get_logger('lib')


@attr.s
class ProtocolParameters(object):
    '''Parameters that are the same for all pathways'''
    clamp = attr.ib(type=str)
    circuit = attr.ib(type=Circuit)
    targets = attr.ib(type=Circuit)
    num_pairs = attr.ib(type=dict)
    num_trials = attr.ib(type=dict)
    dump_amplitudes = attr.ib(type=bool)
    dump_traces = attr.ib(type=bool)
    output_dir = attr.ib(type=str)


def run(
    pathway_files, blueconfig, targets, output_dir, num_pairs, num_trials,
    clamp='current', dump_traces=False, dump_amplitudes=False, seed=None, jobs=None
):
    """ Obtain PSP amplitudes; derive scaling factors """
    # pylint: disable=too-many-arguments

    if clamp == 'voltage' and dump_amplitudes:
        raise PSPError("Voltage clamp mode; Can't pass --dump-amplitudes flag")

    np.random.seed(seed)

    protocol_params = ProtocolParameters(clamp,
                                         Circuit(blueconfig),
                                         load_yaml(targets),
                                         num_pairs,
                                         num_trials,
                                         dump_amplitudes,
                                         dump_traces,
                                         output_dir)

    for pathway_config_path in pathway_files:
        sim_runner = partial(run_pair_simulation_suite,
                             blue_config=blueconfig,
                             base_seed=seed,
                             n_trials=num_trials,
                             n_jobs=jobs,
                             clamp=clamp,
                             log_level=get_logger().level
                             )

        Pathway(pathway_config_path, sim_runner, protocol_params).run()
