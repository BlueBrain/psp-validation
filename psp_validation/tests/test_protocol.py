
from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools

import psp_validation.protocol as prot


def test_instantiate_Protocol() :
    
    protocol = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)


def test_instantiate_Protocol_keyword() :
    
    protocol = prot.Protocol(holding_I = 1, 
                                holding_V = 2, 
                                t_stim = 3, 
                                t_stop = 4, 
                                g_factor =5, 
                                record_dt = 6, 
                                post_ttx = 7, 
                                clamp_V = 8)



def test_Protocol_members() :
    
    p = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)
    ntools.assert_equal(p.holding_I, 1)
    ntools.assert_equal(p.holding_V, 2)
    ntools.assert_equal(p.t_stim, 3)
    ntools.assert_equal(p.t_stop, 4)
    ntools.assert_equal(p.g_factor, 5)
    ntools.assert_equal(p.record_dt, 6)
    ntools.assert_equal(p.post_ttx, 7)
    ntools.assert_equal(p.clamp_V, 8)

def test_Protocol_members_keyword() :

    p = prot.Protocol(holding_I = 1, 
                      holding_V = 2, 
                      t_stim = 3, 
                      t_stop = 4, 
                      g_factor =5, 
                      record_dt = 6, 
                      post_ttx = 7, 
                      clamp_V = 8)

    ntools.assert_equal(p.holding_I, 1)
    ntools.assert_equal(p.holding_V, 2)
    ntools.assert_equal(p.t_stim, 3)
    ntools.assert_equal(p.t_stop, 4)
    ntools.assert_equal(p.g_factor, 5)
    ntools.assert_equal(p.record_dt, 6)
    ntools.assert_equal(p.post_ttx, 7)
    ntools.assert_equal(p.clamp_V, 8)


def test_instantiate_Protocol_equality() :
    
    p0 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)
    p1 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)
    p2 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 42)
    ntools.assert_equal(p0, p1)
    ntools.assert_false(p0 == p2)


def test_instantiate_Protocol_inequality() :
    
    p0 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)
    p1 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 8)
    p2 = prot.Protocol(1, 2, 3, 4, 5, 6, 7, 42)
    ntools.assert_not_equal(p0, p2)
    ntools.assert_true(p0 != p2)
    ntools.assert_false(p0 != p1)


