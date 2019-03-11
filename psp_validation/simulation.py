""" Running pair simulations. """

import os
import collections

import joblib
import numpy as np

from psp_validation import get_logger, setup_logging


LOGGER = get_logger('simulation')


def _ensure_list(v):
    """ Convert iterable / wrap scalar into list. """
    if isinstance(v, collections.Iterable):
        return list(v)
    else:
        return [v]


def _bglibpy():
    import bglibpy
    if 'BGLIBPY_RNG_MODE' in os.environ:
        bglibpy.rngsettings.default_rng_mode = os.environ['BGLIBPY_RNG_MODE']
    return bglibpy


def run_pair_simulation(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_I=None, hold_V=None, post_ttx=False, projection=None, log_level=None
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
        postsynaptic cell soma voltage / injected current trace [(Y, t) tuple]
    """
    # pylint: disable=too-many-arguments,too-many-locals
    if log_level is not None:
        setup_logging(log_level)

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)...', pre_gid, post_gid, base_seed)

    ssim = _bglibpy().ssim.SSim(blue_config, record_dt=record_dt, base_seed=base_seed)
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

    t = post_cell.get_time()

    if hold_I is None:
        y = post_cell.get_recording('clamp_i')
    else:
        y = post_cell.get_soma_voltage()

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)... done', pre_gid, post_gid, base_seed)

    return y, t


def run_pair_simulation_suite(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_V=None, post_ttx=False, clamp='current', projection=None,
    n_trials=1, n_jobs=None
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

    k-th trial would use (`base_seed` + k) as base seed; k=0..N-1.

    Returns:
        N x 2 x T numpy array with trials voltage / current traces (Y_k, t_k)
    """
    # pylint: disable=too-many-arguments,too-many-locals
    assert clamp in ('current', 'voltage')
    if clamp == 'current':
        LOGGER.info("Calculating a%d holding current...", post_gid)
        hold_I, _ = _bglibpy().holding_current(  # pylint: disable=no-member
            hold_V, post_gid, blue_config, enable_ttx=post_ttx
        )
        LOGGER.info("a%d holding current: %.3f nA", post_gid, hold_I)
    else:
        hold_I = None

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    result = joblib.Parallel(n_jobs=n_jobs, backend='loky')([
        joblib.delayed(run_pair_simulation)(
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

    return np.array(result)
