"""Regression tests for input_resistance module

These tests do not test correctness. They are purely for regressions.
Note: these tests are very slow. See if the functionality can be factored
out into smaller testable units.
"""

from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools
import numpy as np
import bluepy
from psp_validation import input_resistance as ir
import os

_bconfig = 'psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling'

circuit_path = bluepy.Simulation(_bconfig).circuit.config.path

class ResistanceCalculatorMgr(object) :

    def __init__(self) :
        self._rc = None
    
    def get_ResistanceCalculator(self) :
        if self._rc is None :
            self._rc = ir.ResistanceCalculator(1, circuit_path, -0.05, 0.05, 3)
        return self._rc

_rc = ResistanceCalculatorMgr()

def test_ResistanceCalculator_instantiate() :

    rc = _rc.get_ResistanceCalculator() 


def test_ResistanceCalculator_voltages() :

    rc = _rc.get_ResistanceCalculator() 
    v = rc.voltages()
    ntools.assert_equal(len(v), 3)
    ntools.assert_equal(v, [-77.423632352051087, -75.086162733631937, -72.710321876448788])


def test_ResistanceCalculator_resistance_function() :

    rc = _rc.get_ResistanceCalculator() 
    rf = rc.resistance_function()
    ntools.assert_equal(rf, 'R(v) = 0.488451477291v + 107.369356749')
    ntools.assert_equal(rc.rmp, -73.899937216430445)
    ntools.assert_equal(len(rc.resistances()), 3)
    ntools.assert_equal(rc.resistances(), [69.54851997111551, 70.699657134034908, 71.850794296954319])

