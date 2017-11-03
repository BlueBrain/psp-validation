#+++++++++++++++++++++++++++++++++++++++++++++++#
#              input_resistance                 #
#-----------------------------------------------#
# Given a gid, this program finds the input     #
# resistance as a function of the input voltage #
#-----------------------------------------------#
# Author: Drew Minnear                          #
# Last Modified: 29.11.2012                     #
#+++++++++++++++++++++++++++++++++++++++++++++++#

# imports for bglibpy and bluepy
import os
import bglibpy
import bluepy
from bluepy.targets.mvddb import Neuron, MType, to_gid_list
import numpy as np
import multiprocessing as mp
from itertools import repeat
import logging

LOGGER = logging.getLogger(__name__)

# this is needed below due to a limitation multiprocessing.map
def mp_iv_point(args_tuple):
    return bglibpy.calculate_SS_voltage_subprocess(*args_tuple)


class ResistanceCalculator:

    def __init__(self, neuron_gid, circuit_config_path, initial_current, final_current, num_data_points, multiproc = False):
        # initialize circuit and gid
        bc = bluepy.Circuit(circuit_config_path)
        self.gid = neuron_gid

        # set default params for current
        initial_current = initial_current
        final_current = final_current
        num_points = num_data_points
        increment = (abs(initial_current) + abs(final_current))/float(num_points)
        self.multiproc = multiproc
        self.currents = [initial_current+ i*increment for i in xrange(0, num_points) if not initial_current+ i*increment == 0]

        self._voltages = None
        self._resistances = None

        # get template and morphology of gid
        m = bc.mvddb
        neuron = list(m.get_gids([self.gid]))[0]
        self.template = str(os.path.join(bc.config.Run.METypePath, neuron.METype+'.hoc'))
        self.morphology = os.path.join(bc.config.Run.MorphologyPath, 'ascii/')


    def resistance_function(self):
        import numpy
        (m, b) = np.polyfit(self.voltages(), self.resistances(), 1)
        return "R(v) = " + str(m) + "v + " + str(b)


    def resistances(self) :
        if self._resistances == None :
            self._init_resistances()
        return self._resistances


    def voltages(self) :
        if self._voltages == None :
            self._init_voltages()
        return self._voltages


    def _init_voltages(self) :
        LOGGER.info('_init_voltages: gid=%d, # of items = %s', self.gid, len(self.currents+[0]))
        v = None
        if self.multiproc :
            pool = mp.Pool()
            v = pool.map(mp_iv_point, zip(repeat(self.template), repeat(self.morphology), self.currents+[0]))
            pool.close()
        else :
            v = [bglibpy.calculate_SS_voltage_subprocess(self.template, self.morphology, i) for i in self.currents+[0]]

        self._voltages = v[:-1]
        self.rmp = v[-1]

        LOGGER.info('_init_voltages: voltages calculated for gid=%d', self.gid)


    def _init_resistances(self) :
        LOGGER.info('_init_resistances: gid=%d', self.gid)
        # make second degree approximation to V-I curve
        (a, b, c) = np.polyfit(self.currents, self.voltages(), 2)

        # compute resistances based on currents and derivative of V-I curve
        self._resistances = [2*a*current + b for current in self.currents]

        LOGGER.debug('_init_resistances: gid=%d, resistances=%s', self.gid, self._resistances)

    def holding_current(self, v_hold, xtol=0.001):
        """ use input resistance to compute approximate holding current, then bisect to get it more accurate
        rtol is relative tolerance in root

        v_hold is in mV
        current is in nA

        """

        LOGGER.info('holding_current: gid=%d', self.gid)
        from scipy.optimize import bisect

        # find current whose v is closest to zero but negative for left
        # positive for right

        def iv(i):
            v = bglibpy.calculate_SS_voltage_subprocess(self.template,
                                                        self.morphology,
                                                        i,
                                                        check_for_spiking=True)
            # v will be None if the cell spiked,
            # and return large diference above v_holding
            if v is None:
                return 20.0
            else:
                return v-v_hold

        # estimate region of root
        (m, b) = np.polyfit(self.currents, self.voltages(), 1)
        center = (v_hold-b)/m

        dx = 1.5
        a = center - dx/m
        b = center + dx/m

        # zoom in a bit
        failed = False
        while iv(a)*iv(b)>=0:
            dx -= 0.25
            LOGGER.debug("iv(a)*iv(b)>=0 -> dx dec to dx=%f", dx)
            a = center - dx/m
            b = center + dx/m
            if dx <= 0.25:
                failed = True
                break
        if failed:
            failed = False
            dx = 1.5
            while iv(a)*iv(b)>=0:
                dx += 0.25
                LOGGER.debug("iv(a)*iv(b)>=0 -> dx inc to dx=%f", dx)
                a = center - dx/m
                b = center + dx/m
                if dx >= 3.25:
                    failed = True
                    break
        if failed:
            raise ValueError, "Could not find endpoints for bisect"

        ret= bisect(iv, a, b, xtol=xtol, maxiter=100)
        LOGGER.debug('holding_current: calculated HC=%s for gid=%d', ret, self.gid)
        return ret

