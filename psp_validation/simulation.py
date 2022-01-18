"""Running pair simulations."""

import logging
import os
import warnings

import attr
import joblib

from psp_validation import setup_logging, PSPError
from psp_validation.utils import ensure_list, isolate

LOGGER = logging.getLogger(__name__)


@attr.s
class SimulationResult(object):
    """Parameters that are the same for all pathways."""
    params = attr.ib()
    time = attr.ib()
    currents = attr.ib()
    voltages = attr.ib()


def _bglibpy(level):
    # pylint: disable=import-outside-toplevel
    import bglibpy
    if 'BGLIBPY_RNG_MODE' in os.environ:
        bglibpy.rngsettings.default_rng_mode = os.environ['BGLIBPY_RNG_MODE']

    #  mapping from https://bbpteam.epfl.ch/project/issues/browse/NSETM-548
    #  16/Sep/19 2:15 PM
    if level < logging.INFO:
        bglibpy.set_verbose(0)
    elif level == logging.INFO:
        bglibpy.set_verbose(2)
    elif level == logging.DEBUG:
        bglibpy.set_verbose(10)

    return bglibpy


def get_holding_current(log_level, hold_V, post_gid, blue_config, post_ttx):
    """Retrieve the holding current using bglibpy."""
    hold_I, _ = _bglibpy(log_level).holding_current(  # pylint: disable=no-member
        hold_V, post_gid, blue_config, enable_ttx=post_ttx
    )
    # If the memory allocated by bglibpy for the simulation is not automatically freed,
    # consider to call gc.collect() here. See NSETM-1356 and BGLPY-80 for more information.
    return hold_I


def _get_synapse_unique_value(cell, getter):
    """Return a value that is supposed to be the same accross all synapses.

    Args:
        cell: a cell
        getter: the getter function to be applied to each synapse
    """
    values = {getter(synapse) for synapse in cell.synapses.values()}
    if not len(values) == 1:
        raise PSPError('Synaptic value is expected to be uniform among all synapses'
                       f' but there are multiple values: {values}')
    return values.pop()


def run_pair_simulation(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_I=None, hold_V=None, post_ttx=False,
    add_projections=False, nrrp=None, log_level=logging.WARNING
):
    """
    Run single pair simulation trial.

    Args:
        blue_config: path to BlueConfig
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
    # pylint: disable=too-many-arguments,too-many-locals
    setup_logging(log_level)

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)...', pre_gid, post_gid, base_seed)

    bg = _bglibpy(log_level)
    ssim = bg.ssim.SSim(blue_config, record_dt=record_dt, base_seed=base_seed, rng_mode='Random123')

    if nrrp is not None:
        ssim.bc.add_section("Connection", "NrrpOverride",
                            {"Source": "Mosaic",
                             "Destination": "Mosaic",
                             "SynapseConfigure": f"%s.Nrrp = {nrrp}"})

    ssim.instantiate_gids(
        [post_gid],
        add_replay=False,
        add_minis=False,
        add_stimuli=False,
        add_synapses=True,
        pre_spike_trains={pre_gid: ensure_list(t_stim)},
        intersect_pre_gids=[pre_gid],
        add_projections=add_projections
    )
    post_cell = ssim.cells[post_gid]

    if _get_synapse_unique_value(post_cell, lambda synapse: synapse.is_inhibitory()):
        first_synapse = next(iter(post_cell.synapses.values())).hsynapse
        if not hasattr(first_synapse, 'e_GABAA'):
            raise PSPError('Inhibitory reverse potential e_GABAA is expected to be under '
                           '"e_GABAA" synaptic range NEURON variable')
        params = {'e_GABAA': _get_synapse_unique_value(
            post_cell, lambda synapse: synapse.hsynapse.e_GABAA)}
    else:
        if not hasattr(bg.neuron.h, 'e_ProbAMPANMDA_EMS'):
            raise PSPError('Excitatory reverse potential e_AMPA is expected to be under '
                           '"e_ProbAMPANMDA_EMS" global NEURON variable')
        params = {'e_AMPA': bg.neuron.h.e_ProbAMPANMDA_EMS}

    if post_ttx:
        post_cell.enable_ttx()

    if hold_I is None:
        # voltage clamp
        post_cell.add_voltage_clamp(
            stop_time=t_stop, level=hold_V, rs=0.001,
            current_record_name='clamp_i'
        )
    else:
        # current clamp
        # add pre-calculated current to set the holding potential
        post_cell.add_ramp(0, 10000, hold_I, hold_I)

    if 'ForwardSkip' in ssim.bc.Run:
        warnings.warn('ForwardSkip found in config file but will disabled for this simulation.'
                      ' (SSCXDIS-229)')

    ssim.run(t_stop=t_stop, dt=0.025, v_init=hold_V, forward_skip=False)

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)... done', pre_gid, post_gid, base_seed)

    return (params,
            post_cell.get_time(),
            post_cell.get_recording('clamp_i') if hold_I is None else hold_I,
            post_cell.get_soma_voltage())


def run_pair_simulation_suite(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_V=None, post_ttx=False, clamp='current', add_projections=False,
    n_trials=1, n_jobs=None,
    log_level=logging.WARNING
):
    """
    Run single pair simulation suite (i.e. multiple trials).

    Args:
        blue_config: path to BlueConfig
        pre_gid: presynaptic GID
        post_gid: postsynaptic GID
        t_stop: run simulation until `t_stop`
        t_stim: pre_gid spike time(s) [single float or list of floats]
        record_dt: timestep of the simulation
        base_seed: simulation base seed
        hold_V: holding voltage (mV)
        post_ttx: emulate TTX effect on postsynaptic cell (i.e. block Na channels)
        clamp: type of the clamp used ['current' | 'voltage']
        add_projections: Whether to enable projections from BlueConfig. Default is False.
        n_trials: number of trials to run
        n_jobs: number of jobs to run in parallel (None for sequential runs)
        log_level: logging level

    k-th trial would use (`base_seed` + k) as base seed; k=0..N-1.

    Returns:
        N x 2 x T numpy array with trials voltage / current traces (Y_k, t_k)
    """
    # pylint: disable=too-many-arguments,too-many-locals

    assert clamp in ('current', 'voltage')
    if clamp == 'current':
        LOGGER.info("Calculating a%d holding current...", post_gid)
        hold_I = get_holding_current(log_level, hold_V, post_gid, blue_config, post_ttx)
        LOGGER.info("a%d holding current: %.3f nA", post_gid, hold_I)
    else:
        hold_I = None

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    # Isolate `run_pair_simulation` in its own process.
    # Note: this is required because bglibpy uses NEURON, and the latter
    #   cannot be coerced to clean up its memory usage; thus causing out of
    #   memory problems as more simulations are run across multiple workers.
    # Note: for debugging purposes, run_pair_simulation should be called directly.
    worker = joblib.delayed(isolate(run_pair_simulation))
    results = joblib.Parallel(n_jobs=n_jobs, backend='loky')([
        worker(
            blue_config=blue_config,
            pre_gid=pre_gid,
            post_gid=post_gid,
            t_stop=t_stop,
            t_stim=t_stim,
            record_dt=record_dt,
            hold_I=hold_I,
            hold_V=hold_V,
            post_ttx=post_ttx,
            add_projections=add_projections,
            log_level=log_level,
            base_seed=(base_seed + k),
        )
        for k in range(n_trials)
    ])

    return SimulationResult(
        params=results[0][0],
        time=results[0][1],
        currents=[result[2] for result in results],
        voltages=[result[3] for result in results]
    )
