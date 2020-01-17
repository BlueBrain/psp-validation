""" Running pair simulations. """

import collections
import logging
import os

import attr
import joblib

from psp_validation import get_logger, setup_logging

LOGGER = get_logger('simulation')


@attr.s
class SimulationResult(object):
    '''Parameters that are the same for all pathways'''
    params = attr.ib()
    time = attr.ib()
    currents = attr.ib()
    voltages = attr.ib()


def _ensure_list(v):
    """ Convert iterable / wrap scalar into list. """
    if isinstance(v, collections.Iterable):
        return list(v)
    else:
        return [v]


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


def get_synapse_unique_value(cell, getter):
    '''Return a value that is supposed to be the same accross all synapses

    Args:
        cell: a cell
        getter: the getter function to be applied to each synapse
    '''
    values = list({getter(synapse) for synapse in cell.synapses.values()})
    if not len(values) == 1:
        raise AssertionError('Expected one value, got {}.\nHere are the values'
                             '{}'.format(len(values), values))
    return values[0]


def run_pair_simulation(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_I=None, hold_V=None, post_ttx=False, projection=None, log_level=logging.WARNING
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
        projection: projection name (None for main connectome)
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

    ssim.instantiate_gids(
        [post_gid],
        add_replay=False,
        add_minis=False,
        add_stimuli=False,
        add_synapses=True,
        pre_spike_trains={pre_gid: _ensure_list(t_stim)},
        intersect_pre_gids=[pre_gid],
        projection=projection
    )
    post_cell = ssim.cells[post_gid]

    if get_synapse_unique_value(post_cell, lambda synapse: synapse.is_inhibitory()):
        params = {'e_GABAA': get_synapse_unique_value(
            post_cell, lambda synapse: synapse.hsynapse.e_GABAA)}
    else:
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
        post_cell.add_ramp(0, 10000, hold_I, hold_I, dt=0.025)

    ssim.run(t_stop=t_stop, dt=0.025, v_init=hold_V)

    time = post_cell.get_time()

    voltage = post_cell.get_soma_voltage()

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)... done', pre_gid, post_gid, base_seed)

    return (params,
            time,
            post_cell.get_recording('clamp_i') if hold_I is None else hold_I,
            voltage)


def run_pair_simulation_suite(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_V=None, post_ttx=False, clamp='current', projection=None,
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
        projection: projection name (None for main connectome)
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
        hold_I, _ = _bglibpy(log_level).holding_current(  # pylint: disable=no-member
            hold_V, post_gid, blue_config, enable_ttx=post_ttx
        )
        LOGGER.info("a%d holding current: %.3f nA", post_gid, hold_I)
    else:
        hold_I = None

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    worker = joblib.delayed(run_pair_simulation)
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
            projection=projection,
            log_level=get_logger().level,
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
