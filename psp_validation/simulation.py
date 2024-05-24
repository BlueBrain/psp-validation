"""Running pair simulations."""

import logging

import attr
import joblib

from psp_validation import PSPError, setup_logging
from psp_validation.utils import ensure_list, isolate

L = logging.getLogger(__name__)


@attr.s
class SimulationResult:
    """Parameters that are the same for all pathways."""

    params = attr.ib()
    time = attr.ib()
    currents = attr.ib()
    voltages = attr.ib()


def _bluecellulab(level):
    import bluecellulab  # noqa: PLC0415 import outside top-level
    import bluecellulab.tools  # noqa: PLC0415 import outside top-level

    if level <= logging.CRITICAL:
        bluecellulab.set_verbose(0)
    elif level == logging.ERROR:
        bluecellulab.set_verbose(1)
    elif level == logging.WARNING:
        bluecellulab.set_verbose(2)
    elif level == logging.INFO:
        bluecellulab.set_verbose(3)
    elif level == logging.DEBUG:
        bluecellulab.set_verbose(10)

    return bluecellulab


def get_holding_current(log_level, hold_V, post_gid, sonata_simulation_config, post_ttx):  # noqa: N803 (argument lowercase)
    """Retrieve the holding current using bluecellulab."""
    hold_i, _ = _bluecellulab(log_level).tools.holding_current(
        hold_V, post_gid, sonata_simulation_config, enable_ttx=post_ttx
    )
    # If the memory allocated by bluecellulab for the simulation is not automatically freed,
    # consider to call gc.collect() here. See NSETM-1356 and BGLPY-80 for more information.
    return hold_i


def _get_synapse_unique_value(cell, getter):
    """Return a value that is supposed to be the same across all synapses.

    Args:
        cell: a cell
        getter: the getter function to be applied to each synapse
    """
    values = {getter(synapse) for synapse in cell.synapses.values()}
    if not len(values) == 1:
        raise PSPError(
            "Synaptic value is expected to be uniform among all synapses"
            f" but there are multiple values: {values}",
        )
    return values.pop()


def run_pair_simulation(  # noqa: PLR0913,PLR0917 too many args / positional args
    sonata_simulation_config,
    pre_gid,
    post_gid,
    t_stop,
    t_stim,
    record_dt,
    base_seed,
    hold_I=None,  # noqa: N803 (argument lowercase)
    hold_V=None,  # noqa: N803 (argument lowercase)
    post_ttx=False,
    add_projections=False,
    nrrp=None,
    log_level=logging.WARNING,
):
    """Run single pair simulation trial.

    Args:
        sonata_simulation_config: path to Sonata simulation config
        pre_gid: presynaptic GID
        post_gid: postsynaptic GID
        t_stop: run simulation until `t_stop`
        t_stim: pre_gid spike time(s) [single float or list of floats]
        record_dt: timestep of the simulation
        base_seed: simulation base seed
        hold_I: holding current [nA] (if None, voltage clamp is applied)
        hold_V: holding voltage [mV]
        post_ttx: emulate TTX effect on postsynaptic cell (i.e. block Na channels)
        add_projections: Whether to enable projections from BlueConfig. Default is False.
        nrrp: Number of vesicles in the Release Ready Pool
        log_level: logging level

    Returns:
        A 4-tuple (params, time, current, voltage)
        time and voltage are arrays of the same size
        In voltage clamp current is an array
        In current clamp it is a scalar at the clamped value
    """
    setup_logging(log_level)

    L.info("sim_pair: %s -> %s (seed=%d)...", pre_gid, post_gid, base_seed)

    bluecellulab = _bluecellulab(log_level)

    sonata_simulation_config = bluecellulab.circuit.config.SonataSimulationConfig(
        str(sonata_simulation_config),
    )
    if nrrp is not None:
        sonata_simulation_config.add_connection_override(
            bluecellulab.circuit.config.sections.ConnectionOverrides(
                source="All",
                target="All",
                synapse_configure=f"%s.Nrrp = {nrrp}",
            ),
        )

    simulation = bluecellulab.circuit_simulation.CircuitSimulation(
        sonata_simulation_config,
        record_dt=record_dt,
        base_seed=base_seed,
        rng_mode="Random123",
    )
    simulation.instantiate_gids(
        post_gid,
        add_replay=False,
        add_minis=False,
        add_stimuli=False,
        add_synapses=True,
        pre_spike_trains={pre_gid: ensure_list(t_stim)},
        intersect_pre_gids=[pre_gid],
        add_projections=add_projections,
    )
    post_cell = simulation.cells[post_gid]

    if _get_synapse_unique_value(  # True, if all synapses are GabaabSynapse
        post_cell, lambda synapse: isinstance(synapse, bluecellulab.synapse.GabaabSynapse)
    ):
        first_synapse = next(iter(post_cell.synapses.values())).hsynapse
        if not hasattr(first_synapse, "e_GABAA"):
            raise PSPError(
                "Inhibitory reverse potential e_GABAA is expected to be under "
                '"e_GABAA" synaptic range NEURON variable',
            )
        params = {
            "e_GABAA": _get_synapse_unique_value(
                post_cell, lambda synapse: synapse.hsynapse.e_GABAA
            ),
        }
    else:  # If none of the synapses are GabaabSynapse
        if not hasattr(bluecellulab.neuron.h, "e_ProbAMPANMDA_EMS"):
            raise PSPError(
                "Excitatory reverse potential e_AMPA is expected to be under "
                '"e_ProbAMPANMDA_EMS" global NEURON variable',
            )
        params = {"e_AMPA": bluecellulab.neuron.h.e_ProbAMPANMDA_EMS}

    if post_ttx:
        post_cell.enable_ttx()

    if hold_I is None:
        # voltage clamp
        post_cell.add_voltage_clamp(
            stop_time=t_stop, level=hold_V, rs=0.001, current_record_name="clamp_i"
        )
    else:
        # current clamp
        # add pre-calculated current to set the holding potential
        post_cell.add_ramp(0, 10000, hold_I, hold_I)

    simulation.run(t_stop=t_stop, dt=0.025, v_init=hold_V, forward_skip=False)

    L.info("sim_pair: %s -> %s (seed=%d)... done", pre_gid, post_gid, base_seed)

    return (
        params,
        post_cell.get_time(),
        post_cell.get_recording("clamp_i") if hold_I is None else hold_I,
        post_cell.get_soma_voltage(),
    )


def run_pair_simulation_suite(  # noqa: PLR0913,PLR0917 too many args / positional args
    sonata_simulation_config,
    pre_gid,
    post_gid,
    t_stop,
    t_stim,
    record_dt,
    base_seed,
    hold_V=None,  # noqa: N803 (argument lowercase)
    post_ttx=False,
    clamp="current",
    add_projections=False,
    n_trials=1,
    n_jobs=None,
    log_level=logging.WARNING,
):
    """Run single pair simulation suite (i.e. multiple trials).

    Args:
        sonata_simulation_config: path to Sonata simulation config
        pre_gid: presynaptic GID
        post_gid: postsynaptic GID
        t_stop: run simulation until `t_stop`
        t_stim: pre_gid spike time(s) [single float or list of floats]
        record_dt: timestep of the simulation
        base_seed: simulation base seed
        hold_V: holding voltage (mV)
        post_ttx: emulate TTX effect on postsynaptic cell (i.e. block Na channels)
        clamp: type of the clamp used ['current' | 'voltage']
        add_projections: Whether to enable projections. Default is False.
        n_trials: number of trials to run
        n_jobs: number of jobs to run in parallel (None for sequential runs)
        log_level: logging level

    k-th trial would use (`base_seed` + k) as base seed; k=0..N-1.

    Returns:
        N x 2 x T numpy array with trials voltage / current traces (Y_k, t_k)
    """
    assert clamp in {"current", "voltage"}
    if clamp == "current":
        L.info("Calculating %s holding current...", post_gid)
        hold_i = get_holding_current(
            log_level, hold_V, post_gid, sonata_simulation_config, post_ttx
        )
        L.info("%s holding current: %.3f nA", post_gid, hold_i)
    else:
        hold_i = None

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    # Isolate `run_pair_simulation` in its own process.
    # Note: this is required because bluecellulab uses NEURON, and the latter
    #   cannot be coerced to clean up its memory usage; thus causing out of
    #   memory problems as more simulations are run across multiple workers.
    # Note: for debugging purposes, run_pair_simulation should be called directly.
    worker = joblib.delayed(isolate(run_pair_simulation))
    results = joblib.Parallel(n_jobs=n_jobs, backend="loky")(
        [
            worker(
                sonata_simulation_config=sonata_simulation_config,
                pre_gid=pre_gid,
                post_gid=post_gid,
                t_stop=t_stop,
                t_stim=t_stim,
                record_dt=record_dt,
                hold_I=hold_i,
                hold_V=hold_V,
                post_ttx=post_ttx,
                add_projections=add_projections,
                log_level=log_level,
                base_seed=(base_seed + k),
            )
            for k in range(n_trials)
        ],
    )

    return SimulationResult(
        params=results[0][0],
        time=results[0][1],
        currents=[result[2] for result in results],
        voltages=[result[3] for result in results],
    )
