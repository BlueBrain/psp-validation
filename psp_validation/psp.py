"""
Check the amplitude of the compound *E*PSP; works only with excitatory
synapses at this time. However, no checks are done to see if you actually
specified an excitatory synapse. Be carefull.
Minis are not used because they provide too much noise.
No current injection other than the current to achieve the holding potential
are included. (no HypAmp for instance)
"""
import logging
from functools import partial

import attr
from bluepysnap import Simulation, Circuit
import numpy as np

from psp_validation import PSPError
from psp_validation.pathways import Pathway
from psp_validation.simulation import run_pair_simulation_suite
from psp_validation.utils import load_yaml

L = logging.getLogger(__name__)


@attr.s
class ProtocolParameters:
    """Parameters that are the same for all pathways."""
    clamp = attr.ib(type=str)
    circuit = attr.ib(type=Circuit)
    targets = attr.ib(type=Circuit)
    num_pairs = attr.ib(type=dict)
    num_trials = attr.ib(type=dict)
    dump_amplitudes = attr.ib(type=bool)
    dump_traces = attr.ib(type=bool)
    output_dir = attr.ib(type=str)


def run(
    pathway_files, sonata_simulation_config, targets, output_dir, num_pairs, num_trials,
    edge_population, clamp='current', dump_traces=False, dump_amplitudes=False, seed=None, jobs=None
):
    """ Obtain PSP amplitudes; derive scaling factors """
    # pylint: disable=too-many-arguments

    if clamp == 'voltage' and dump_amplitudes:
        raise PSPError("Voltage clamp mode; Can't pass --dump-amplitudes flag")

    np.random.seed(seed)

    protocol_params = ProtocolParameters(clamp,
                                         Simulation(sonata_simulation_config).circuit,
                                         load_yaml(targets),
                                         num_pairs,
                                         num_trials,
                                         dump_amplitudes,
                                         dump_traces,
                                         output_dir)

    for pathway_config_path in pathway_files:
        sim_runner = partial(run_pair_simulation_suite,
                             sonata_simulation_config=sonata_simulation_config,
                             base_seed=seed,
                             n_trials=num_trials,
                             n_jobs=jobs,
                             clamp=clamp,
                             log_level=L.getEffectiveLevel(),
                             )

        Pathway(pathway_config_path, sim_runner, protocol_params, edge_population).run()
