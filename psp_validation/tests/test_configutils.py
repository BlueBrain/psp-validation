
from sys import path as _path
if '.' not in _path :
    _path.append('.')

import random
from nose import tools as ntools

import psp_validation.configutils as cfg


def test_checkAttributesMatching() :

    d = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4 }
    attrs = ['c', 'd', 'a', 'b']
    for i in xrange(10) :
        random.shuffle(attrs)
        cfg.check_attributes(d, attrs)

@ntools.raises(AttributeError)
def test_checkAttributesNonMatchingRaises() :

    d = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4 }
    attrs = ['c', 'd', 'a', 'f']
    for i in xrange(10) :
        random.shuffle(attrs)
        cfg.check_attributes(d, attrs)


@ntools.raises(AttributeError)
def test_checkAttributesMissingAttrRaises() :

    d = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4 }
    attrs = ['c', 'd', 'a', 'd', 'e']
    cfg.check_attributes(d, attrs)


@ntools.raises(AttributeError)
def test_checkAttributesTooManyAttrsRaises() :

    d = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4, 'e' : 5 }
    attrs = ['c', 'd', 'a', 'd']
    cfg.check_attributes(d, attrs)


def test_load_json_from_string() :
    
    json_data = '{"a" : 1, "b" : 2, "c" : 3, "d" : 4, "e" : 5 }'
    json_obj = cfg.load_json(json_data)
    cfg.check_attributes(json_obj, ('a', 'b', 'c', 'd', 'e'))
    ntools.assert_equal(json_obj['a'], 1)
    ntools.assert_equal(json_obj['b'], 2)
    ntools.assert_equal(json_obj['c'], 3)
    ntools.assert_equal(json_obj['d'], 4)
    ntools.assert_equal(json_obj['e'], 5)


def test_configFromJson() :
    
    json_data = '{"a" : 1, "b" : 2, "c" : 3, "d" : 4, "e" : 5 }'
    json_obj = cfg.load_json(json_data)
    config = cfg.config_from_json(json_obj)

    ntools.assert_equal(config.a, 1)
    ntools.assert_equal(config.b, 2)
    ntools.assert_equal(config.c, 3)
    ntools.assert_equal(config.d, 4)
    ntools.assert_equal(config.e, 5)


def test_json2protocol_valid() :
    
    json_data = '{"holding_I" : 1, "holding_V" : 2, "t_stim" : 3, "t_stop" : 4, "g_factor" : 5, "record_dt" : 6, "post_ttx" : 7, "clamp_V" :8}'
 
    config = cfg.json2protocol(json_data)

    ntools.assert_equal(config.holding_I, 1)
    ntools.assert_equal(config.holding_V, 2)
    ntools.assert_equal(config.t_stim, 3)
    ntools.assert_equal(config.t_stop, 4)
    ntools.assert_equal(config.g_factor, 5)
    ntools.assert_equal(config.record_dt, 6)
    ntools.assert_equal(config.post_ttx, 7)
    ntools.assert_equal(config.clamp_V, 8)


@ntools.raises(AttributeError)
def test_protocolFromJson_invalid_raises() :
    
    json_data = '{"holding_I" : 1, "holding_V" : 2, "t_stop" : 4, "g_factor" : 5, "record_dt" : 6, "post_ttx" : 7, "clamp_V" :8}'
 
    config = cfg.json2protocol(json_data)


def test_json2simconfig_valid() :

    json_data = '{"pathways" : ["blah", "blah"], "n_pairs" : 3, "rndm_seed" : 42, "n_repetitions" : 5, "output_dir" : "/dev/null", "blue_config" : "foo/bar/baz", "multiprocessing" : true, "protocols" : ["a", "b"]}'

    simcfg = cfg.json2simconfig(json_data)
    ntools.assert_equal(simcfg.pathways, ["blah", "blah"])
    ntools.assert_equal(simcfg.n_pairs, 3)
    ntools.assert_equal(simcfg.rndm_seed, 42)
    ntools.assert_equal(simcfg.n_repetitions, 5)
    ntools.assert_equal(simcfg.output_dir, '/dev/null')
    ntools.assert_equal(simcfg.blue_config, 'foo/bar/baz')
    ntools.assert_equal(simcfg.multiprocessing, True)
    ntools.assert_equal(simcfg.protocols, ["a", "b"])


@ntools.raises(AttributeError)
def test_json2simconfig_invalid_raises() :

    json_data = '{"n_pairs" : 3, "rndm_seed" : 42, "n_repetitions" : 5, "output_dir" : "/dev/null", "blue_config" : "foo/bar/RefBlueConfig_Scaling", "multiprocessing" : 1, "protocols" : ["a", "b"]}'

    simcfg = cfg.json2simconfig(json_data)

