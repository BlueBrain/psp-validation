"""Repository for pathway queries."""
import itertools
import logging
import os
from builtins import filter

import h5py
import numpy as np
from bluepy.enums import Cell

from psp_validation.features import (
    compute_scaling,
    get_peak_amplitudes,
    get_synapse_type,
    mean_pair_voltage_from_traces,
    old_school_trace,
    resting_potential,
)
from psp_validation.persistencyutils import dump_pair_traces
from psp_validation.trace_filters import AmplitudeFilter, NullFilter, SpikeFilter
from psp_validation.utils import load_config

LOGGER = logging.getLogger(__name__)


class ConnectionFilter:
    """Filter (pre_gid, post_gid, [nsyn]) tuples by different criteria.

    Args:
        circuit: bluepy.Circuit instance

        unique_gids: use GIDs only once
        min_nsyn: min synapse count for connection
        max_nsyn: max synapse count for connection
        max_dist_x: max distance along X axis between pre- and post- synaptic soma
        max_dist_y: max distance along Y axis between pre- and post- synaptic soma
        max_dist_z: max distance along Z axis between pre- and post- synaptic soma

    NB:
        * using `unique_gids` makes ConnectionFilter stateful
        * using `min_syn` or `max_syn` requires (pre_gid, post_gid, nsyn) input tuples
    """

    def __init__(
        self, circuit, unique_gids=False, min_nsyn=None, max_nsyn=None,
        max_dist_x=None, max_dist_y=None, max_dist_z=None
    ):
        self.circuit = circuit
        self.min_nsyn = min_nsyn
        self.max_nsyn = max_nsyn
        self.max_dist_x = max_dist_x
        self.max_dist_y = max_dist_y
        self.max_dist_z = max_dist_z
        if unique_gids:
            self.used_gids = set()
        else:
            self.used_gids = None

    def __call__(self, conn):
        # pylint: disable=too-many-return-statements,too-many-branches
        pre_gid, post_gid = conn[:2]
        if self.used_gids is not None:
            if (pre_gid in self.used_gids) or (post_gid in self.used_gids):
                return False
        if self.min_nsyn is not None:
            if conn[2] < self.min_nsyn:
                return False
        if self.max_nsyn is not None:
            if conn[2] > self.max_nsyn:
                return False
        if self.max_dist_x is not None:
            x1, x2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.X]
            if abs(x1 - x2) > self.max_dist_x:
                return False
        if self.max_dist_y is not None:
            y1, y2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.Y]
            if abs(y1 - y2) > self.max_dist_y:
                return False
        if self.max_dist_z is not None:
            z1, z2 = self.circuit.cells.get([pre_gid, post_gid])[Cell.Z]
            if abs(z1 - z2) > self.max_dist_z:
                return False
        if self.used_gids is not None:
            self.used_gids.add(pre_gid)
            self.used_gids.add(post_gid)
        return True

    @property
    def requires_synapse_count(self):
        """ If filter uses synapse count. """
        return (self.min_nsyn is not None) or (self.max_nsyn is not None)


def get_pairs(circuit, pre, post, n_pairs, constraints=None, projection=None):
    """Get 'n_pairs' connected pairs specified by `query` and optional `constraints`.

    Args:
        circuit: bluepy.Circuit instance
        pre: presynaptic cell group (BluePy query)
        post: postsynaptic cell group (BluePy query)
        n_pairs: number of pairs to return
        constraints: dict passed as kwargs to `ConnectionFilter`
        projection: projection name (None for main connectome)

    Returns:
        List of `n` (pre_gid, post_gid) pairs (or fewer if could not find enough)
    """
    if projection is None:
        connectome = circuit.connectome
    else:
        connectome = circuit.projection(projection)

    filt, return_synapse_count = None, False
    if constraints is not None:
        filt = ConnectionFilter(circuit, **constraints)
        return_synapse_count = filt.requires_synapse_count

    iter_connections = connectome.iter_connections(
        pre=pre, post=post,
        shuffle=True,
        return_synapse_count=return_synapse_count
    )
    if filt is not None:
        iter_connections = filter(filt, iter_connections)

    return [conn[:2] for conn in itertools.islice(iter_connections, n_pairs)]


def _get_pathway_pairs(pathway, circuit, num_pairs, projection, targets):
    """Get 'num_pairs' of gids for the given pathway.

    Returns:
        List of (pre_gid, post_gid) pairs
    """
    if 'pairs' in pathway:
        for item in pathway['pairs']:
            assert isinstance(item, list) and len(item) == 2
        return pathway['pairs']
    else:
        LOGGER.info("Querying pathway pairs...")

        def get_target(name):
            """Get target."""
            return targets.get(name, name)

        pre = get_target(pathway['pre'])
        post = get_target(pathway['post'])
        return get_pairs(
            circuit, pre, post, num_pairs,
            constraints=pathway.get('constraints'),
            projection=projection
        )


class Pathway:
    """Pathway specific parameters.

    A pathway is all connections between given pre post cell types.
    When doing psp-validation we sample from this pathway (we dont use all connection),
    but that's how we use the term: "pathway".

    A connection is a sample from the pathway, or all synapses between given pre and post single
    cells

    Synapse is just one synapse from the connection (as a connection can be mediated by multiple
    synapses
    """

    def __init__(self, pathway_config_path, sim_runner, protocol_params):
        """The pathway constructor.

        The simulation is run only when ``run`` method is called.

        Args:
            pathway_config_path (str): path to a pathway file
            sim_runner (function): a callable to run the simulation
            protocol_params (ProtocolParameters): the parameters to used

        Attrs:
            title: the pathway name, taken from the basename of the pathway file
            config: the config
            sim_runner: a callable that will run the simulation and return traces
            protocol_params: the parameters describing the experimental protocol
            pathway: a dictionary with the pathway specific information
            projection: projection
            pairs: the list of gid pairs
            t_stim: numeric scalar representing stimulation time.
            t_start: the simulation start time
            trace_filters: list of filters to filter out voltage traces
            resting_potentials: the resting potentials
        """
        self.title, self.config = load_config(pathway_config_path)
        self.sim_runner = sim_runner
        self.protocol_params = protocol_params
        LOGGER.info("Processing '%s' pathway...", self.title)

        self.pathway = self.config['pathway']
        self.projection = self.pathway.get('projection')

        self.pairs = _get_pathway_pairs(self.pathway, protocol_params.circuit,
                                        protocol_params.num_pairs,
                                        self.projection,
                                        protocol_params.targets)

        if self.projection is None:
            self.pre_syn_type = get_synapse_type(protocol_params.circuit,
                                                 [p[0] for p in self.pairs])
        else:
            self.pre_syn_type = "EXC"

        self.min_ampl = self.config.get('min_amplitude', 0.0)
        self.min_trace_ampl = self.config.get('min_trace_amplitude', 0.0)  # NSETM-1166

        self.t_stim = self.config['protocol']['t_stim']
        if isinstance(self.t_stim, list):
            # in case of input spike train, use first spike time as split point
            self.t_stim = min(self.t_stim)

        self.t_start = self.t_stim - 10.
        self.trace_filters = [
            NullFilter(),
            SpikeFilter(t_start=self.t_start, v_max=-20),
            AmplitudeFilter(
                t_stim=self.t_stim,
                min_trace_amplitude=self.min_trace_ampl,
                syn_type=self.pre_syn_type,
            ),
        ]
        self.resting_potentials = []

    def run(self):
        """Run the simulation for the given pathway."""
        if self.protocol_params.dump_traces:
            traces_path = self._init_traces_dump()
        else:
            traces_path = None

        if not self.pairs:
            return

        all_amplitudes = []
        for i_pair in range(len(self.pairs)):
            params = self._run_one_pair(i_pair, all_amplitudes, traces_path)

        if self.protocol_params.clamp != 'current':
            return

        if self.protocol_params.dump_amplitudes:
            np.savetxt(os.path.join(self.protocol_params.output_dir,
                                    self.title + ".amplitudes.txt"),
                       all_amplitudes, fmt="%.9f")

        self._write_summary(params, all_amplitudes)

    def _run_one_pair(self, i_pair, all_amplitudes, traces_path):
        """
        Runs the simulation for a given pair, extract the peak amplitude and
        write the trace to disk if protocol_params.dump_traces.

        Args:
            i_pair (int): the pair index in the list of pairs
            all_amplitudes: a list that will store all amplitudes
            traces_path: the trace path
        """
        # pylint: disable=too-many-locals
        pre_gid, post_gid = self.pairs[i_pair]
        sim_results = self.sim_runner(
            pre_gid=pre_gid, post_gid=post_gid,
            add_projections=bool(self.config['pathway'].get('projection')),
            **self.config['protocol'])

        traces, average = self._post_run(pre_gid, post_gid, sim_results, all_amplitudes)

        if self.protocol_params.dump_traces:
            with h5py.File(traces_path, 'a') as h5f:
                dump_pair_traces(h5f, traces, average, pre_gid, post_gid)

        return sim_results.params

    def _post_run(self, pre_gid, post_gid, sim_results, all_amplitudes):
        """Returns a tuple (all traces, averaged trace).

        Where trace is a voltage in current clamp mode, a current in voltage clamp mode

        Also:
            - fill the all_amplitudes list
            - Compute the resting potential if the holding voltage is None

        In case of voltage traces, they are filtered to calculate the average,
        but the returned traces are not filtered.
        """
        if self.protocol_params.clamp == 'current':
            traces = old_school_trace(sim_results)
            v_mean, t, v_used = mean_pair_voltage_from_traces(traces, self.trace_filters)

            filtered_count = len(sim_results.voltages) - len(v_used)
            if filtered_count > 0:
                LOGGER.warning("%d out of %d traces filtered out for a%d-a%d"
                               " simulation(s) due to spiking or synaptic failure",
                               filtered_count, len(sim_results.voltages),
                               pre_gid, post_gid
                               )
            if v_mean is None:
                LOGGER.warning("Could not extract PSP amplitude for a%d-a%d pair due to spiking",
                               pre_gid, post_gid)
                average = None
                ampl = np.nan
            else:
                average = np.stack([v_mean, t])
                ampl = get_peak_amplitudes([t], [v_mean], self.t_stim, self.pre_syn_type)[0]
                if ampl < self.min_ampl:
                    LOGGER.warning(
                        "PSP amplitude below given threshold for a%d-a%d pair (%.3g < %.3g)",
                        pre_gid, post_gid, ampl, self.min_ampl
                    )
                    ampl = np.nan

                # Use resting potential instead of hold_V when the later is None for the
                # scaling computation: see NSETM-637
                if 'reference' in self.config and self.config['protocol']['hold_V'] is None:
                    self.resting_potentials.append(resting_potential(
                        t, v_mean, self.t_start, self.t_stim))

            all_amplitudes.append(ampl)
        else:
            average = np.stack([np.mean(sim_results.currents, axis=0),
                                sim_results.time])
            traces = sim_results.currents

        return traces, average

    def _init_traces_dump(self):
        """Create empty H5 dump or overwrite existing one."""
        traces_path = os.path.join(self.protocol_params.output_dir,
                                   self.title + ".traces.h5")
        with h5py.File(traces_path, 'w') as h5f:
            h5f.attrs['version'] = '1.1'
            # we store voltage traces for current clamp and vice-versa
            h5f.attrs['data'] = {
                'current': 'voltage',
                'voltage': 'current',
            }[self.protocol_params.clamp]
        return traces_path

    def _write_summary(self, params, all_amplitudes):
        model_mean = np.nanmean(all_amplitudes)
        model_std = np.nanstd(all_amplitudes)

        reference, scaling = self._get_reference_and_scaling(model_mean, params)

        summary_path = os.path.join(self.protocol_params.output_dir,
                                    self.title + ".summary.yaml")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(
                f"pathway: {self.title}\n"
                f"model:\n"
                f"    mean: {model_mean}\n"
                f"    std: {model_std}\n"
            )
            if reference is not None:
                f.write(
                    f"reference:\n"
                    f"    mean: {reference['mean']}\n"
                    f"    std: {reference['std']}\n"
                )
            if scaling is not None:
                f.write(f"scaling: {scaling}\n")

    def _get_reference_and_scaling(self, model_mean, params):
        if 'reference' in self.config:
            reference = self.config['reference']['psp_amplitude']
            v_holding = self.config['protocol']['hold_V']
            if v_holding is None:
                v_holding = np.mean(self.resting_potentials)
            scaling = compute_scaling(model_mean, reference['mean'], v_holding, self.pre_syn_type,
                                      params)
        else:
            reference = None
            scaling = None
        return reference, scaling
