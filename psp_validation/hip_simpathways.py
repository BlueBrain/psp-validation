#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper classes and functions to simulate PSP traces and calculate their amplitude.
Pair selection process replaced by Giuseppe's bbuutils.targetselector
Eilif's script see (simpathways.py) modified by Andras for the hippocampal circuit (02.2017)
"""

import bluepy
from holding_current import mp_holding_current
import multiprocessing as mp
from itertools import repeat
import numpy
import warnings
import psp
from copy import copy
import logging
import bbputils.targetselector

LOGGER = logging.getLogger(__name__)


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def _eq_cmp(lhs, rhs):
    """Compare two elements for equality.

    Perform element-wise comparison for numpy arrays.
    """
    return numpy.all(lhs == rhs)


class PairSelection(object):
    """Placeholder class holding together pair selection parameters.
    """

    def __init__(self, pair_filter, d_cut):

        for key, val in locals().iteritems():
            if not key == 'self':
                setattr(self, key, val)

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


class SimConfig(object):
    """Holds simulation configuration parameters for PathwayEPhys
    Class holding sub-set of simulation configuration parameters
    required for PathwayEPhys
    """
    def __init__(self, sim_config):
        _attrs = ('blue_config', 'n_pairs', 'rndm_seed',
                  'n_repetitions', 'multiprocessing')
        for attr in _attrs:
            setattr(self, attr, getattr(sim_config, attr))

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)


class PathwayEPhys(object):
    """Mega class that does far, far too much.
    Any attempt to understand this is futile.
    """
    def __init__(self,
                 pathway,
                 protocol,
                 sim_config):

        self.pathway = copy(pathway)
        self.protocol = protocol
        self.sim_config = copy(sim_config)
        self.circuit_path = bluepy.Simulation(self.sim_config.blue_config).circuit.config.path
        self.circuit = bluepy.Circuit(self.circuit_path)
        self._holding_iv = None
        self._holding_currents = None
        self._pairs = None
        self._amplitudes = None
        self._traces = None
        self.syn_map = None

    def __str__(self):
        #return "\nPathwayEphys object:\npathway: %s\nprotocol: %s\nsim_config: %s\ncircuit_path: %s\n"%(self.pathway, self.protocol, self.sim_config, self.circuit_path)
        return "\npathway: %s"%(self.pathway)

    def traces(self):
        """Get PSP simulation traces for each pair
        Uses lazy evaluation. Only calculated once, then cached.
        """
        if self._traces is None:
            self._compute_traces()
        return self._traces

    def pairs(self):
        """Get list of cell pairs
        Uses lazy evaluation. Only calculated once, then cached.
        """
        if self._pairs is None:
            self._set_pairs()
        return self._pairs

    def holding_currents(self):
        """Get holding currents
        Uses lazy evaluation. Only calculated once, then cached.
        """
        if self._holding_iv is None:
            self._compute_holding_currents()
        return self._holding_currents

    def psp_amplitudes(self):
        """Get pair-wise peak PSP amplitudes
        Uses lazy evaluation. Only calculated once, then cached.
        """
        if self._amplitudes is None:
            self._compute_psp_amplitudes()
        return self._amplitudes

    def extract_metypenames(self):
        """This is absolutly not elegant, but necessary function to merge Eilif's and Giuseppe's script easily
        (extracts MType name from pathway query)      
        """
        import re   

        start_s = 'MType.name=="'
        end_s = '"'
        assert start_s in self.pathway.presynaptic_cell_query, "Only MType.name like querying is implemented so far ..."
        assert start_s in self.pathway.postsynaptic_cell_query, "Only MType.name like querying is implemented so far ..."
        preCell = re.search('%s(.*)%s' % (start_s, end_s), self.pathway.presynaptic_cell_query).group(1)
        postCell = re.search('%s(.*)%s' % (start_s, end_s), self.pathway.postsynaptic_cell_query).group(1)

        return preCell, postCell


    def _set_pairs(self):
        """Get the list of cell pairs for this pathway, using Giuseppe's bbputils (updated by Andras 01.2017)"""

        n_pairs = self.sim_config.n_pairs

        # def. targetselector object
        tselector = bbputils.targetselector.Selector(self.circuit_path)
        tselector.setseed(self.sim_config.rndm_seed)

        # define constraints
        # TODO: make this work with specific pathways (not constructed from MType.name) - see them in hip_pathways.py !!!!!
        preCell, postCell = self.extract_metypenames()
        pregid_config = {'mtype':preCell}
        postgid_config = {'mtype':postCell}

        constraints = {'max_dist_x': 200.0, 'max_dist_y': 200.0,'max_dist_z': 100.0}  # dcut=100. before factoring out... -> 'max_dist_z':100

        # select pairs
        pairs = tselector.getrandompairs(pregid_config, postgid_config, constraints=constraints, n=n_pairs, show_progress=True)  # list of tuples
        if len(pairs) < n_pairs:
            warnings.warn("Too few pairs (%d of %d) found for pathway %s->%s"%(len(pairs), n_pairs, preCell, postCell))
        pairs = numpy.array(pairs[:n_pairs])
        
        numpy.random.seed(self.sim_config.rndm_seed)
        self._pairs = pairs[numpy.random.permutation(len(pairs)), :]
        # previously this was an n_pair x 3 array, now it's just n_pairs x 2 (pre and post gid), but the 3rd argument isn't used anywhere
        LOGGER.debug('_set_pairs:\n%s', self._pairs)


    def _compute_holding_currents(self):
        """
        If v_holding != None, compute holding_currents and re-compute v_holding.
        Otherwise set holding_currents to list of None.
        """      
        LOGGER.info('_compute_holdings: cpu count = %s', mp.cpu_count())
        if self.protocol.holding_V is None:
            self._holding_iv = None
            self._holding_currents = [None] * len(self.pairs())
        else:
            work_items = zip(repeat(self.protocol.holding_V),
                             self.pairs()[:, 1],
                             repeat(self.circuit_path))
                             #repeat(self.sim_config.multiprocessing))  # multiprocessing can't be passed, since these processes would be childs of daemonic processes (and python won't let that happen) -> the holding current will be calculated in a serial manner -> multiproc is powefull if you calculate many pairs with a lot of repetitions... - Andras 
            LOGGER.info('_compute_holding_currents: multiprocess %s items', len(work_items))
            LOGGER.debug('_compute_holding_currents: items = %s', work_items)
            mp_pool = mp.Pool(mp.cpu_count())
            self._holding_iv = mp_pool.map(mp_holding_current, work_items)
            mp_pool.close()
            self._holding_currents = [x[0] for x in self._holding_iv]

        LOGGER.debug('_holding_currents: %s', self._holding_currents)


    def _compute_traces(self):
        """Compute PSP traces
        """
        work_items = self._work_items()
        LOGGER.info('compute_traces with %s work items', len(work_items))
        self._traces = [psp.run_pair_trace_simulations(*wi,
                                                       hold_V=self.protocol.holding_V,
                                                       t_stim=self.protocol.t_stim,
                                                       t_stop=self.protocol.t_stop,
                                                       g_factor=self.protocol.g_factor,
                                                       record_dt=self.protocol.record_dt,
                                                       post_ttx=self.protocol.post_ttx,
                                                       v_clamp=self.protocol.clamp_V,
                                                       spikes=None,
                                                       rndm_seed=self.sim_config.rndm_seed,
                                                       repetitions=self.sim_config.n_repetitions,
                                                       use_multiprocessing=self.sim_config.multiprocessing)
                        for wi in work_items]

    def _compute_psp_amplitudes(self):
        """Perform calculation of PSP amplitudes
        """
        t_start = self.protocol.t_stim - 10
        v_max = -20
        trace_filter = psp.SpikeFilter(t_start, v_max)

        synapse_types = [psp.synapse_type(self.sim_config.blue_config, p)
                         for p in self.pairs()[:, 0]]
        work_items = zip(self.traces(),
                         synapse_types,
                         repeat(trace_filter),
                         repeat(self.protocol.t_stim))
        self._amplitudes = [psp.calculate_amplitude(*wi) for wi in work_items]
        return self._amplitudes

    def _work_items(self):
        """Make a tuple of parameters
        """
        items = zip(repeat(self.sim_config.blue_config),
                    self.pairs()[:, 0],
                    self.pairs()[:, 1],
                    self.holding_currents())
        LOGGER.debug('_work_items: %s', items)
        return items


    def __eq__(self, rhs):
        attrs = ('pathway', 'protocol', 'circuit_path',
                 '_holding_currents', '_holding_iv', '_pairs',
                 '_traces', '_amplitudes')
        for attr in attrs:
            if not _eq_cmp(self.__getattribute__(attr),
                           rhs.__getattribute__(attr)):
                return False
        return True

    def __ne__(self, rhs):
        return not self.__eq__(rhs)
