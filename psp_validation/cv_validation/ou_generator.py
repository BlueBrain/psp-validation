"""Adds Ornstein-Uhlenbeck (OU) noise to current/voltage traces.

For BBP references see Barros-Zulaica et al. 2019 and Ecker et al. 2020

author: András Ecker
"""

import numpy as np


def ou_generator(time, tau, sigma, initial_noise=0):
    """Generates OU noise using forward Euler

    Args:
        time: numpy array - representing time
        tau: float - tau parameter of OU noise (extracted from in vitro traces)
        sigma: float - sigma parameter of OU noise (extracted from in vitro traces)
        initial_noise: float - mean/initial value of the noise
    """
    datalen = time.shape[0]
    dt = time[1] - time[0]
    noise = np.zeros(datalen, dtype=np.float32)
    noise[0] = initial_noise

    # Precalculate these as they don't have to be (re)calculated in the loop
    dt_tau = dt / tau
    random_element = np.random.normal(size=datalen) * sigma * np.sqrt(2 * dt_tau)

    for i in range(1, datalen):
        noise[i] = noise[i - 1] + dt_tau * (noise[0] - noise[i - 1]) + random_element[i - 1]

    return noise


def add_ou_noise(time, traces, tau, sigma):
    """Adds noise to current/voltage traces (see also `ou_generator()`)"""
    for i in range(traces.shape[0]):
        traces[i, :] += ou_generator(time, tau, sigma)
    return traces
