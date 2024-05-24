"""Repository for pathway queries."""

import itertools
import logging

import h5py
import numpy as np

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

L = logging.getLogger(__name__)


class ConnectionFilter:
    """Filter (pre_gid, post_gid, [nsyn]) tuples by different criteria."""

    def __init__(
        self,
        edge_population,
        unique_gids=False,
        min_nsyn=None,
        max_nsyn=None,
        max_dist_x=None,
        max_dist_y=None,
        max_dist_z=None,
    ):
        """The ConnectionFilter constructor.

        Args:
            edge_population: bluepysnap.edges.EdgePopulation instance

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
        self.edge_population = edge_population
        self.min_nsyn = min_nsyn
        self.max_nsyn = max_nsyn
        self.max_dist_x = max_dist_x
        self.max_dist_y = max_dist_y
        self.max_dist_z = max_dist_z
        if unique_gids:
            self.used_gids = set()
        else:
            self.used_gids = None

    def __call__(self, connection):  # noqa: C901,PLR0911 too-complex,too-many-returns
        """Apply filtering"""
        pre_gid, post_gid = connection[:2]
        if self.used_gids is not None and (
            (pre_gid in self.used_gids) or (post_gid in self.used_gids)
        ):
            return False
        if self.min_nsyn is not None and (connection[2] < self.min_nsyn):
            return False
        if self.max_nsyn is not None and (connection[2] > self.max_nsyn):
            return False
        if self.max_dist_x is not None:
            x1 = self.edge_population.source.get(pre_gid, "x")
            x2 = self.edge_population.target.get(post_gid, "x")
            if abs(x1 - x2) > self.max_dist_x:
                return False
        if self.max_dist_y is not None:
            y1 = self.edge_population.source.get(pre_gid, "y")
            y2 = self.edge_population.target.get(post_gid, "y")
            if abs(y1 - y2) > self.max_dist_y:
                return False
        if self.max_dist_z is not None:
            z1 = self.edge_population.source.get(pre_gid, "z")
            z2 = self.edge_population.target.get(post_gid, "z")
            if abs(z1 - z2) > self.max_dist_z:
                return False
        if self.used_gids is not None:
            self.used_gids.add(pre_gid)
            self.used_gids.add(post_gid)
        return True

    @property
    def requires_synapse_count(self):
        """If filter uses synapse count."""
        return (self.min_nsyn is not None) or (self.max_nsyn is not None)


def get_pairs(edge_population, pre, post, num_pairs, constraints=None):
    """Get 'n_pairs' connected pairs specified by `query` and optional `constraints`.

    Args:
        edge_population: bluepysnap.edges.EdgePopulation instance
        pre: presynaptic node set
        post: postsynaptic node set
        num_pairs: number of pairs to return
        constraints: dict passed as kwargs to `ConnectionFilter`

    Returns:
        List of `n` (pre_gid, post_gid) pairs (or fewer if could not find enough)
    """
    L.info("Sampling pairs for pathway...")
    constraints = constraints or {}
    connection_filter = ConnectionFilter(edge_population, **constraints)

    iter_connections = edge_population.iter_connections(
        pre, post, shuffle=True, return_edge_count=connection_filter.requires_synapse_count
    )

    iter_connections = filter(connection_filter, iter_connections)
    pairs = [connection[:2] for connection in itertools.islice(iter_connections, num_pairs)]

    if not pairs:
        L.warning("Could not find pairs for the pathway")

    return pairs


class Pathway:
    """Pathway specific parameters.

    A pathway is all connections between given pre post cell types.
    When doing psp-validation we sample from this pathway (we don't use all connection),
    but that's how we use the term: "pathway".

    A connection is a sample from the pathway, or all synapses between given pre and post single
    cells

    Synapse is just one synapse from the connection (as a connection can be mediated by multiple
    synapses
    """

    def __init__(self, pathway_config_path, sim_runner, protocol_params, edge_population):
        """The pathway constructor.

        The simulation is run only when ``run`` method is called.

        Args:
            pathway_config_path (pathlib.Path): path to a pathway file
            sim_runner (function): a callable to run the simulation
            protocol_params (ProtocolParameters): the parameters to used
            edge_population (str): edge population name

        Attrs:
            title: the pathway name, taken from the basename of the pathway file
            config: the config
            sim_runner: a callable that will run the simulation and return traces
            protocol_params: the parameters describing the experimental protocol
            pathway: a dictionary with the pathway specific information
            pairs: the list of gid pairs
            t_stim: numeric scalar representing stimulation time.
            t_start: the simulation start time
            trace_filters: list of filters to filter out voltage traces
            resting_potentials: the resting potentials
        """
        self.title = pathway_config_path.stem
        self.config = load_config(pathway_config_path)
        self.sim_runner = sim_runner
        self.protocol_params = protocol_params
        L.info("Processing '%s' pathway...", self.title)

        self.pathway = self.config["pathway"]

        pre = self.protocol_params.targets.get(self.pathway["pre"], self.pathway["pre"])
        post = self.protocol_params.targets.get(self.pathway["post"], self.pathway["post"])
        circuit = protocol_params.circuit

        self.edge_population = circuit.edges[edge_population]

        self.pairs = get_pairs(
            self.edge_population,
            pre,
            post,
            num_pairs=protocol_params.num_pairs,
            constraints=self.pathway.get("constraints"),
        )

        self.pre_syn_type = get_synapse_type(self.edge_population.source, pre)

        self.min_ampl = self.config.get("min_amplitude", 0.0)
        self.min_trace_ampl = self.config.get("min_trace_amplitude", 0.0)  # NSETM-1166

        self.t_stim = self.config["protocol"]["t_stim"]
        if isinstance(self.t_stim, list):
            # in case of input spike train, use first spike time as split point
            self.t_stim = min(self.t_stim)

        self.t_start = self.t_stim - 10.0
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
        traces_path = self._init_traces_dump() if self.protocol_params.dump_traces else None

        if not self.pairs:
            L.warning("No pairs to run.")
            return

        all_amplitudes = []
        for pair in self.pairs:
            params = self._run_one_pair(pair, all_amplitudes, traces_path)

        if self.protocol_params.clamp != "current":
            return

        if self.protocol_params.dump_amplitudes:
            np.savetxt(
                self.protocol_params.output_dir / f"{self.title}.amplitudes.txt",
                all_amplitudes,
                fmt="%.9f",
            )

        self._write_summary(params, all_amplitudes)

    def _has_projections(self):
        """Check if the edge population of the pathway contains projections"""
        edge_type = self.edge_population.type
        pre_type = self.edge_population.source.type
        post_type = self.edge_population.target.type

        return (edge_type, pre_type, post_type) == ("chemical", "virtual", "biophysical")

    def _run_one_pair(self, pair, all_amplitudes, traces_path):
        """Run the simulation for a given pair.

        Also, extract the peak amplitude and write the trace to disk if protocol_params.dump_traces.

        Args:
            pair (int): a pair of node ids
            all_amplitudes: a list that will store all amplitudes
            traces_path: the trace path
        """
        pre_gid, post_gid = pair
        sim_results = self.sim_runner(
            pre_gid=pre_gid,
            post_gid=post_gid,
            add_projections=self._has_projections(),
            **self.config["protocol"],
        )

        traces, average = self._post_run(pre_gid, post_gid, sim_results, all_amplitudes)

        if self.protocol_params.dump_traces:
            with h5py.File(traces_path, "a") as h5f:
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
        if self.protocol_params.clamp == "current":
            traces = old_school_trace(sim_results)
            v_mean, t, v_used = mean_pair_voltage_from_traces(traces, self.trace_filters)

            filtered_count = len(sim_results.voltages) - len(v_used)
            if filtered_count > 0:
                L.warning(
                    "%d out of %d traces filtered out for %s-%s"
                    " simulation(s) due to spiking or synaptic failure",
                    filtered_count,
                    len(sim_results.voltages),
                    pre_gid,
                    post_gid,
                )
            if v_mean is None:
                L.warning(
                    "Could not extract PSP amplitude for %s-%s pair due to spiking",
                    pre_gid,
                    post_gid,
                )
                average = None
                ampl = np.nan
            else:
                average = np.stack([v_mean, t])
                ampl = get_peak_amplitudes([t], [v_mean], self.t_stim, self.pre_syn_type)[0]
                if ampl < self.min_ampl:
                    L.warning(
                        "PSP amplitude below given threshold for %s-%s pair (%.3g < %.3g)",
                        pre_gid,
                        post_gid,
                        ampl,
                        self.min_ampl,
                    )
                    ampl = np.nan

                # Use resting potential instead of hold_V when the later is None for the
                # scaling computation: see NSETM-637
                if "reference" in self.config and self.config["protocol"]["hold_V"] is None:
                    self.resting_potentials.append(
                        resting_potential(t, v_mean, self.t_start, self.t_stim),
                    )

            all_amplitudes.append(ampl)
        else:
            average = np.stack([np.mean(sim_results.currents, axis=0), sim_results.time])
            traces = sim_results.currents

        return traces, average

    def _init_traces_dump(self):
        """Create empty H5 dump or overwrite existing one."""
        traces_path = self.protocol_params.output_dir / f"{self.title}.traces.h5"
        with h5py.File(traces_path, "w") as h5f:
            h5f.attrs["version"] = "1.1"
            # we store voltage traces for current clamp and vice-versa
            h5f.attrs["data"] = {
                "current": "voltage",
                "voltage": "current",
            }[self.protocol_params.clamp]
        return traces_path

    def _write_summary(self, params, all_amplitudes):
        model_mean = np.nanmean(all_amplitudes)
        model_std = np.nanstd(all_amplitudes)

        reference, scaling = self._get_reference_and_scaling(model_mean, params)

        summary_path = self.protocol_params.output_dir / f"{self.title}.summary.yaml"
        summary = (
            f"pathway: {self.title}\n"
            "model:\n"
            f"    mean: {model_mean}\n"
            f"    std: {model_std}\n"
        )
        if reference is not None:
            summary += f"reference:\n    mean: {reference['mean']}\n    std: {reference['std']}\n"

        if scaling is not None:
            summary += f"scaling: {scaling}\n"

        summary_path.write_text(summary)

    def _get_reference_and_scaling(self, model_mean, params):
        if "reference" in self.config:
            reference = self.config["reference"]["psp_amplitude"]
            v_holding = self.config["protocol"]["hold_V"]
            if v_holding is None:
                v_holding = np.mean(self.resting_potentials)
            scaling = compute_scaling(
                model_mean, reference["mean"], v_holding, self.pre_syn_type, params
            )
        else:
            reference = None
            scaling = None
        return reference, scaling
