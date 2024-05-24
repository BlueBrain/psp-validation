"""Trace filters."""

import logging
from abc import ABC, abstractmethod

from psp_validation.features import get_peak_amplitudes, get_peak_voltage

L = logging.getLogger(__name__)


class BaseTraceFilter(ABC):
    """Base trace filter."""

    @abstractmethod
    def __call__(self, traces):
        """Apply the trace filter.

        Args:
            traces (list): N x 2 x T array of traces.
                N: number of traces
                2: voltage and time arrays
                T: number of measurements

        Returns:
            the selected traces
        """


class NullFilter(BaseTraceFilter):
    """Filter out empty or null traces."""

    def __call__(self, traces):
        """Apply the filter."""
        selected = []
        for v_, t_ in traces:
            if v_ is None or len(v_) == 0:
                L.debug("Skip empty or null trace")
                continue
            selected.append((v_, t_))
        return selected


class SpikeFilter(BaseTraceFilter):
    """Filter out traces with spikes."""

    def __init__(self, t_start, v_max):
        """Initialize the filter.

        Args:
            t_start (float): initial time used to detect spikes.
            v_max (float): absolute maximum value used to identify a spike. If a trace contains any
                value above this threshold, then it's filtered out.
        """
        self.t0 = t_start
        self.v_max = v_max

    def __call__(self, traces):
        """Apply the filter."""
        selected = []
        for v_, t_ in traces:
            if get_peak_voltage(t_, v_, self.t0, "EXC") > self.v_max:
                L.debug("Skip trace containing spikes")
                continue
            selected.append((v_, t_))
        return selected


class AmplitudeFilter(BaseTraceFilter):
    """Filter out traces with insufficient amplitude."""

    def __init__(self, t_stim, min_trace_amplitude, syn_type):
        """Initialize the filter.

        Args:
            t_stim (float): time of the stimulus.
            min_trace_amplitude (float): minimum (unsigned) variation required to keep a trace.
                For EXC synapses, the trace is filtered out if
                maximum_voltage < voltage_base + min_trace_amplitude.
                For INH synapses, the trace is filtered out if
                minimum_voltage > voltage_base - min_trace_amplitude.
                Note: maximum_voltage and minimum_voltage are interpolated.
            syn_type: synapse type (EXC or INH).
        """
        self.t_stim = t_stim
        self.min_trace_amplitude = min_trace_amplitude
        self.syn_type = syn_type

    def __call__(self, traces):
        """Apply the filter."""
        if self.min_trace_amplitude <= 0:
            return traces
        insufficient = []
        selected = []
        voltages = [v for v, _ in traces]
        times = [t for _, t in traces]

        amplitudes = get_peak_amplitudes(times, voltages, self.t_stim, self.syn_type)
        for trace, amplitude in zip(traces, amplitudes):
            if amplitude < self.min_trace_amplitude:
                insufficient.append(amplitude)
            else:
                selected.append(trace)

        if insufficient:
            L.debug(
                "Skip trace(s) with insufficient amplitude: %s", ", ".join(map(str, insufficient))
            )
        return selected
