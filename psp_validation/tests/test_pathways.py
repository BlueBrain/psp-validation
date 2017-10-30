from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools

import psp_validation.pathways as pw

# all labels in pathway map
labels = pw._pathways.keys()

def _split_label(label, sep = '-') :
    spl = label.split(sep)
    return spl[0], spl[1]


def test_Pathway_instantiate() :

    s = pw.Pathway(1,2)


def test_Pathway_instantiate_with_keywords() :

    s = pw.Pathway(presynaptic_cell_query = 1, 
                   postsynaptic_cell_query = 2)


def test_Pathway_members() :

    s = pw.Pathway(1,2)
    ntools.assert_equal(s.presynaptic_cell_query, 1)
    ntools.assert_equal(s.postsynaptic_cell_query, 2)


def test_Pathway_members_keywords() :

    e = pw.Pathway(postsynaptic_cell_query = 2, presynaptic_cell_query = 1)
    ntools.assert_equal(e.presynaptic_cell_query, 1)
    ntools.assert_equal(e.postsynaptic_cell_query, 2)


def test_Pathway_equality() :

    e0 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 2)
    e1 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 2)
    e2 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 3)
    ntools.assert_equal(e0, e1)
    ntools.assert_false(e0 == e2)


def test_Pathway_inequality() :

    e0 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 2)
    e1 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 2)
    e2 = pw.Pathway(presynaptic_cell_query = 1, postsynaptic_cell_query = 3)
    ntools.assert_not_equal(e0, e2)
    ntools.assert_true(e0 != e2)
    ntools.assert_false(e0 != e1)


def test_get_pathway_keys() :
    
    for l in labels :
        pway = pw.get_pathway(l)


def test_get_pathway_pre() :
    
    for l in labels :
        pway = pw.get_pathway(l)
        pre, _ = _split_label(l)
        query = pw.__getattribute__(pre)
        ntools.assert_equal(pway.presynaptic_cell_query, query)


def test_get_pathway_post() :
    
    for l in labels :
        pway = pw.get_pathway(l)
        _, post = _split_label(l)
        query = pw.__getattribute__(post)
        ntools.assert_equal(pway.postsynaptic_cell_query, query)
