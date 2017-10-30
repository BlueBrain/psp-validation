from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools
import sqlalchemy as sqla
import bluepy
from bluepy.targets.mvddb import Neuron
from psp_validation import simpathways as pw
from psp_validation import pathways
from psp_validation import protocol
from copy import copy
import numpy as np

class MockConfig(object) :
    
    def __init__(self, **kwargs) :
        for k, v in kwargs.iteritems() :
            setattr(self, k, v)

    def __eq__(self, rhs) :
        attrs = self.__dict__.keys()
        for a in attrs :
            if self.__getattribute__(a) != rhs.__getattribute__(a) :
                return False
        return True


    def __ne__(self, rhs) :
        return not self.__eq__(rhs)



bconfig =  './psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling'


_query = sqla.or_(*(Neuron.miniColumn==mc_id for mc_id in range(620, 930, 5)))

_pselect = pw.PairSelection(pair_filter= None, d_cut = 100)

L5_TTPC = 'Or(MType.name=="L5_TTPC1", MType.name=="L5_TTPC2")'
L5_STPC = 'MType.name=="L5_STPC"'
_pathway = pathways.Pathway(L5_TTPC, L5_TTPC)

_protocol = protocol.Protocol(1,2,3,4,5,6,7,8)

_markram_97 = MockConfig(holding_I = None,
                         holding_V = -67.0,
                         t_stim = 800.0,
                         t_stop = 900.0,
                         g_factor = 1.0,
                         record_dt = 0.1,
                         post_ttx = False,
                         clamp_V = None)


_simconfig = MockConfig(pathways = ['L5_TTPC-L5_TTPC'],
                        protocols = ['foo.json'],
                        n_pairs = 5,
                        rndm_seed = 456,
                        n_repetitions = 5,
                        multiprocessing = True,
                        output_dir = './scratch',
                        blue_config = bconfig)



def _run_chunks(step) :
    c0 = pw.chunks(range(0, 5*step), step)
    counter = 0
    for i, c in enumerate(c0) :
        k = i + counter
        ntools.assert_equal(range(k, k+step), c)
        counter += step - 1


def test_chunks() :
    for step in xrange(2,12) :
        _run_chunks(step)




def test_SimConfig_instantiate() :
    
    sc = pw.SimConfig(_simconfig)


def test_SimConfig_members() :

    sc = pw.SimConfig(_simconfig)
    ntools.assert_equal(sc.blue_config, _simconfig.blue_config)
    ntools.assert_equal(sc.n_pairs, _simconfig.n_pairs)
    ntools.assert_equal(sc.rndm_seed, _simconfig.rndm_seed)
    ntools.assert_equal(sc.n_repetitions, _simconfig.n_repetitions)
    ntools.assert_equal(sc.multiprocessing, _simconfig.multiprocessing)

def test_SomConfig_equality() :

    sc0 = pw.SimConfig(_simconfig)
    sc1 = pw.SimConfig(_simconfig)
    sc2 = pw.SimConfig(_simconfig)
    sc2.n_pairs = 999

    ntools.assert_true(sc0 == sc1)
    ntools.assert_false(sc0 == sc2)


def test_SomConfig_inequality() :

    sc0 = pw.SimConfig(_simconfig)
    sc1 = pw.SimConfig(_simconfig)
    sc2 = pw.SimConfig(_simconfig)
    sc2.n_pairs = 999

    ntools.assert_false(sc0 != sc1)
    ntools.assert_true(sc0 != sc2)


def test_PairSelection_members() :

    pc = pw.PairSelection('foobar', 123)

    ntools.assert_equal(pc.pair_filter, 'foobar')
    ntools.assert_equal(pc.d_cut, 123)



def test_PairSelection_members_keywords() :

    pc = pw.PairSelection(pair_filter= 'foobar', 
                          d_cut = 123)

    ntools.assert_equal(pc.pair_filter, 'foobar')
    ntools.assert_equal(pc.d_cut, 123)


def test_PairSelection_equality() :

    pc0 = pw.PairSelection('foobar', 123)
    pc1 = pw.PairSelection('foobar', 123)
    pc2 = pw.PairSelection('foo', 123)
    pc3 = pw.PairSelection('foobar', 124)

    ntools.assert_equal(pc0, pc1)
    ntools.assert_false(pc0 == pc2)
    ntools.assert_false(pc0 == pc3)
    ntools.assert_false(pc1 == pc2)
    ntools.assert_false(pc1 == pc3)
    ntools.assert_false(pc2 == pc3)


def test_PairSelection_inequality() :

    pc0 = pw.PairSelection('foobar', 123)
    pc1 = pw.PairSelection('foobar', 123)
    pc2 = pw.PairSelection('foo', 123)
    pc3 = pw.PairSelection('foobar', 124)

    ntools.assert_false(pc0 != pc1)
    ntools.assert_not_equal(pc0, pc2)
    ntools.assert_not_equal(pc0, pc3)
    ntools.assert_not_equal(pc2, pc3)



def test_PathwayEPhys_instantiate() :
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _simconfig, _pselect)


def test_PathwayEPhys_members() :

    bcpath_ = bluepy.Simulation(_simconfig.blue_config).circuit.config.path
    circuit_ = bluepy.Circuit(bcpath_)
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _simconfig, _pselect)
    ntools.assert_equal(pw_ephys.pathway, _pathway)
    ntools.assert_equal(pw_ephys.protocol, _protocol)
    ntools.assert_equal(pw_ephys.sim_config, _simconfig)
    ntools.assert_equal(pw_ephys.pair_select, _pselect)
    ntools.assert_equal(pw_ephys.circuit_path, bcpath_)

def test_PathwayEPhys_equality() :

    pw1 = pathways.Pathway(L5_TTPC, L5_TTPC)
    pw2 =pathways.Pathway(L5_TTPC, L5_STPC)
    prot1 = protocol.Protocol(11,12,13,14,15,16,17,18)

    pw_ephys0 = pw.PathwayEPhys(_pathway, _protocol, _simconfig, _pselect)
    pw_ephys1 = pw.PathwayEPhys(pw1, _protocol,  _simconfig, _pselect)
    pw_ephys2 = pw.PathwayEPhys(pw2, _protocol, _simconfig, _pselect)
    pw_ephys3 = pw.PathwayEPhys(pw1, prot1, _simconfig, _pselect)

    ntools.assert_true(pw_ephys0 == pw_ephys1)
    ntools.assert_false(pw_ephys0 == pw_ephys2)
    ntools.assert_false(pw_ephys1 == pw_ephys2)
    ntools.assert_false(pw_ephys0 == pw_ephys3)
    ntools.assert_false(pw_ephys1 == pw_ephys3)


def test_PathwayEPhys_inequality() :

    pw1 = pathways.Pathway(L5_TTPC, L5_TTPC)
    pw2 = pathways.Pathway(L5_TTPC, L5_STPC)
    prot1 = protocol.Protocol(11,12,13,14,15,16,17,18)

    pw_ephys0 = pw.PathwayEPhys(_pathway, _protocol, _simconfig, _pselect)
    pw_ephys1 = pw.PathwayEPhys(pw1, _protocol,  _simconfig, _pselect)
    pw_ephys2 = pw.PathwayEPhys(pw2, _protocol, _simconfig, _pselect)
    pw_ephys3 = pw.PathwayEPhys(pw1, prot1, _simconfig, _pselect)

    ntools.assert_false(pw_ephys0 != pw_ephys1)
    ntools.assert_true(pw_ephys0 != pw_ephys2)
    ntools.assert_true(pw_ephys1 != pw_ephys2)
    ntools.assert_true(pw_ephys0 != pw_ephys3)
    ntools.assert_true(pw_ephys1 != pw_ephys3)
    ntools.assert_not_equal(pw_ephys0, pw_ephys2)
    ntools.assert_not_equal(pw_ephys1, pw_ephys2)
    ntools.assert_not_equal(pw_ephys0, pw_ephys3)
    ntools.assert_not_equal(pw_ephys1, pw_ephys3)



def test_PathwayEPhys_len_pairs() :

    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _simconfig, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 5)


def test_PathwayEPhys_2_pairs() :

    _pw_config = copy(_simconfig)
    _pw_config.n_pairs = 2
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _pw_config, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 2)
    ntools.assert_true(np.all(pw_ephys.pairs() == 
                              np.array([[ 1,  3,  6],
                                        [ 6,  9,  8]])))

def test_PathwayEPhys_3_pairs() :

    _pw_config = copy(_simconfig)
    _pw_config.n_pairs = 3
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _pw_config, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 3)
    ntools.assert_true(np.all(pw_ephys.pairs() ==
                              np.array([[ 1,  3,  6],
                                        [ 6,  9,  8],
                                        [ 1,  5,  7]])))


def test_PathwayEPhys_4_pairs() :

    _pw_config = copy(_simconfig)
    _pw_config.n_pairs = 4
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _pw_config, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 4)
    ntools.assert_true(np.all(pw_ephys.pairs() ==
                              np.array([[ 1,  3,  6],
                                        [ 6,  9,  8],
                                        [ 1,  5,  7],
                                        [ 2,  4,  7]])))


def test_PathwayEPhys_5_pairs() :

    _pw_config = copy(_simconfig)
    _pw_config.n_pairs = 5
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _pw_config, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 5)
    ntools.assert_true(np.all(pw_ephys.pairs() ==
                              np.array([[ 1,  3,  6],
                                        [ 6,  9,  8],
                                        [ 1,  5,  7],
                                        [ 2,  4,  7],
                                        [ 8, 10,  6]])))




def test_PathwayEPhys_all_pairs() :

    _pw_config = copy(_simconfig)
    _pw_config.n_pairs = 100 # huge number, we can't have this many in a 10 cell circuit
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _pw_config, _pselect)
    ntools.assert_equal(len(pw_ephys.pairs()), 6)
    ntools.assert_true(np.all(pw_ephys.pairs() == 
                              np.array([[ 1,  3,  6],
                                        [ 6,  9,  8],
                                        [ 1,  5,  7],
                                        [ 2,  4,  7],
                                        [ 8, 10,  6],
                                        [ 5,  7,  6]])))


def test_PathwayEPhys_holding_currents_None() :

    _sim_cfg = copy(_simconfig)
    _sim_cfg.n_pairs = 2
    _protocol = copy(_markram_97)
    _protocol.holding_V = None
    pw_ephys = pw.PathwayEPhys(_pathway, _protocol, _sim_cfg, _pselect)
    hc = pw_ephys.holding_currents()
    ntools.assert_equal(len(hc), pw_ephys.sim_config.n_pairs)
    ntools.assert_equal(hc, [None, None])

"""
def test_PathwayEPhys_holding_currents() :

    _sim_cfg = copy(_simconfig)
    _sim_cfg.n_pairs = 2
    pw_ephys = pw.PathwayEPhys(_pathway, _markram_97, _sim_cfg, _pselect)
    hc = pw_ephys.holding_currents()
    ntools.assert_equal(len(hc), pw_ephys.sim_config.n_pairs)
    ntools.assert_equal(hc, [0.12685750994745562, 0.10346934551623962])
"""

