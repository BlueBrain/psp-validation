
from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools

import psp_validation.experiment as exp

def test_Stats_instantiate() :

    s = exp.Stats(1,2)


def test_Stats_instantiate_with_keywords() :

    s = exp.Stats(mean = 1, sigma = 2)


def test_Stats_members() :

    s = exp.Stats(1,2)
    ntools.assert_equal(s.mean, 1)
    ntools.assert_equal(s.sigma, 2)


def test_Stats_members_keywords() :

    e = exp.Stats(sigma = 2, mean = 1)
    ntools.assert_equal(e.mean, 1)
    ntools.assert_equal(e.sigma, 2)


def test_Stats_equality() :

    e0 = exp.Stats(mean = 1, sigma = 2)
    e1 = exp.Stats(mean = 1, sigma = 2)
    e2 = exp.Stats(mean = 1, sigma = 3)
    ntools.assert_equal(e0, e1)
    ntools.assert_false(e0 == e2)


def test_Stats_inequality() :

    e0 = exp.Stats(mean = 1, sigma = 2)
    e1 = exp.Stats(mean = 1, sigma = 2)
    e2 = exp.Stats(mean = 1, sigma = 3)
    ntools.assert_not_equal(e0, e2)
    ntools.assert_true(e0 != e2)
    ntools.assert_false(e0 != e1)


def test_Results_instantiate() :
    
    e = exp.Results(exp.Stats(1,2), exp.Stats(3,4))


def test_Results_instantiate_with_keywords() :
    

    e = exp.Results(amplitude_stats = exp.Stats(1,2),
                    synapses_per_connection_stats = exp.Stats(3,4))


def test_Results_members() :
    
    e = exp.Results(exp.Stats(1,2), exp.Stats(3,4))
    ntools.assert_equal(e.amplitude_stats, exp.Stats(1,2))
    ntools.assert_equal(e.synapses_per_connection_stats, exp.Stats(3,4))


def test_Results_members_keyword() :

    e = exp.Results(amplitude_stats = exp.Stats(1,2),
                    synapses_per_connection_stats = exp.Stats(3,4))

    ntools.assert_equal(e.amplitude_stats, exp.Stats(1,2))
    ntools.assert_equal(e.synapses_per_connection_stats, exp.Stats(3,4))



def test_Results_equality() :
    
    e0 = exp.Results(exp.Stats(1,2), exp.Stats(3,4))
    e1 = exp.Results(exp.Stats(1,2), exp.Stats(3,4))
    e2 = exp.Results(exp.Stats(1,2), exp.Stats(5,6))
    ntools.assert_equal(e0, e1)
    ntools.assert_false(e0 == e2)


def test_Results_inequality() :
 
    e0 = exp.Results(exp.Stats(1,2), exp.Stats(3,4))
    e1 = exp.Results(exp.Stats(1,2), exp.Stats(3,4))
    e2 = exp.Results(exp.Stats(1,2), exp.Stats(5,6))
    ntools.assert_not_equal(e0, e2)
    ntools.assert_true(e0 != e2)
    ntools.assert_false(e0 != e1)


_paper_results = {"pwayA" : exp.Results(exp.Stats(1,2), exp.Stats(3,4)),
                  "pwayB" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)) }

def test_Paper_instantiate() :
    
    p = exp.Paper("Paper X", _paper_results)
                  


def test_Paper_instantiate_with_keywords() :
    
    p = exp.Paper(title = "Paper X", results = _paper_results)


def test_Paper_members() :
    p = exp.Paper(title = "Paper X", results = _paper_results)
    ntools.assert_equal(p.title, "Paper X")
    ntools.assert_equal(p.results, _paper_results)


def test_Paper_members_keyword() :

    p = exp.Paper(title = "Paper X", results = _paper_results)
    ntools.assert_equal(p.title, "Paper X")
    ntools.assert_equal(p.results, _paper_results)


def test_Paper_equality() :
    
    p0 = exp.Paper("Paper X", _paper_results)
    p1 = exp.Paper("Paper X", _paper_results)
    p2 = exp.Paper("Paper Y", _paper_results)
    _res = {"pwayC" : exp.Results(exp.Stats(1,2), exp.Stats(3,4)),
            "pwayD" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)) }
    p3 = exp.Paper("Paper Y", _res)
    ntools.assert_equal(p0, p1)
    ntools.assert_false(p0 == p2)
    ntools.assert_false(p0 == p3)


def test_Paper_inequality() :

    p0 = exp.Paper("Paper X", _paper_results)
    p1 = exp.Paper("Paper X", _paper_results)
    p2 = exp.Paper("Paper Y", _paper_results)
    _res = {"pwayC" : exp.Results(exp.Stats(1,2), exp.Stats(3,4)),
            "pwayD" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)) }

    ntools.assert_not_equal(p0, p2)
    ntools.assert_true(p0 != p2)
    ntools.assert_false(p0 != p1)

def test_Paper_getResult() :
    
    p = exp.Paper("Paper X", _paper_results)
    ntools.assert_equal(p.get_result('pwayA'), 
                        exp.Results(exp.Stats(1,2), exp.Stats(3,4)))
    ntools.assert_equal(p.get_result('pwayB'), 
                        exp.Results(exp.Stats(5,6), exp.Stats(7,8)))

def test_Paper_getPathways() :
    
    _res = {
            "pwayA" : exp.Results(exp.Stats(1,2), exp.Stats(3,4)),
            "pwayB" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)),
            "pwayC" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)), 
            "pwayD" : exp.Results(exp.Stats(5,6), exp.Stats(7,8)), 
            }

    p = exp.Paper("Paper X", _res)
    pathways = p.get_pathways()
    ref_pathways = _res.keys()
    ntools.assert_equal(pathways, ref_pathways)
    # let's be explicit just to be sure
    ntools.assert_true('pwayA' in pathways)
    ntools.assert_true('pwayB' in pathways)
    ntools.assert_true('pwayC' in pathways)
    ntools.assert_true('pwayD' in pathways)
    ntools.assert_true(len(pathways) == 4)


