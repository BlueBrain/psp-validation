""" Running pair simulations. """

import collections

import numpy as np

from psp_validation import get_logger


LOGGER = get_logger('simulation')


def _ensure_list(v):
    """ Convert iterable / wrap scalar into list. """
    if isinstance(v, collections.Iterable):
        return list(v)
    else:
        return [v]


def run_pair_simulation(
    blue_config, pre_gid, post_gid,
    t_stop, t_stim, record_dt, base_seed,
    hold_I=None, hold_V=None, post_ttx=False, projection=None
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

    Returns:
        postsynaptic cell soma voltage / injected current trace [(Y, t) tuple]
    """
    # pylint: disable=too-many-arguments,too-many-locals
    import bglibpy

    LOGGER.info('sim_pair: a%d -> a%d (seed=%d)...', pre_gid, post_gid, base_seed)

    ssim = bglibpy.ssim.SSim(blue_config, record_dt=record_dt, base_seed=base_seed)
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


def mp_run_pair_simulation(kwargs):
    """ Forward kwargs to run_pair_simulation. """
    return run_pair_simulation(**kwargs)


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
        import bglibpy
        LOGGER.info("Calculating a%d holding current...", post_gid)
        hold_I, _ = bglibpy.holding_current(hold_V, post_gid, blue_config, enable_ttx=post_ttx)
        LOGGER.info("a%d holding current: %.3f nA", post_gid, hold_I)
    else:
        hold_I = None

    common_args = dict(
        blue_config=blue_config,
        pre_gid=pre_gid,
        post_gid=post_gid,
        t_stop=t_stop,
        t_stim=t_stim,
        record_dt=record_dt,
        hold_I=hold_I,
        hold_V=hold_V,
        post_ttx=post_ttx,
        projection=projection
    )
    run_args = [dict(base_seed=(base_seed + k), **common_args) for k in range(n_trials)]

    if n_jobs is None:
        result = map(mp_run_pair_simulation, run_args)
    else:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        if n_jobs <= 0:
            n_jobs = cpu_count
        else:
            # spawning too many jobs would be inefficient
            n_jobs = min(n_jobs, cpu_count)
        # no need to spawn more jobs than tasks to run
        n_jobs = min(n_jobs, len(run_args))
        pool = multiprocessing.Pool(n_jobs)
        result = pool.map(mp_run_pair_simulation, run_args)
        pool.close()

    return np.array(result)
