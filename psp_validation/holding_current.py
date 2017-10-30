"""Helper functions for holding current, voltage calculation
"""

import logging
import input_resistance as ir

LOGGER = logging.getLogger(__name__)

# this is needed due to a limitation of multiprocessing map in python 2.6
# http://stackoverflow.com/questions/5442910/
# python-multiprocessing-pool-map-for-multiple-arguments
def mp_holding_current(args):
    """Forward args to holding_current.
    """
    return holding_current(*args)


def holding_current(v_hold, gid, circuit_path, xtol=0.0001):
    """ Estimate the holding current to abs tolerance xtol """
    LOGGER.info('holding_current: gid=%d', gid)
    LOGGER.debug('holding_current: calculating with args = %s', locals())
    import bglibpy
    # make resistance calculator object and find resistance function
    calc = ir.ResistanceCalculator(gid,
                                   circuit_path,
                                   initial_current=-0.05,
                                   final_current=0.05,
                                   num_data_points=3)
    #calc.resistance_function()
    i = calc.holding_current(v_hold, xtol=xtol)
    # compute the voltage at the determined holdiung current
    v = bglibpy.calculate_SS_voltage_subprocess(calc.template,
                                                calc.morphology,
                                                i)
    LOGGER.debug('holding_current calculated for gid=%d: i=%f, v=%f, ', gid, i, v)
    return i, v
