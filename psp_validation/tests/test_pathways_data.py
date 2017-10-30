from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools

import psp_validation.pathways_data as pd

# all labels in pathway map
labels = tuple([v.label for k, v in pd.pathways_map.iteritems()])


def test_instantiate_PathwayData() :
    pwd = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "L5_TTPC-L5_TTPC (Markram 97)")   

def test_PathwayData_members() :
    p = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "Hello, World!")   
    ntools.assert_equal(p.pre, 1)
    ntools.assert_equal(p.post, 2)
    ntools.assert_equal(p.v_holding, 3)
    ntools.assert_equal(p.psp, (4,5))
    ntools.assert_equal(p.syns_per_conn, (6,7))
    ntools.assert_equal(p.label, "Hello, World!")

def test_PathwayData_equality() :
    p0 = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "Hello, World!")   
    p1 = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "Hello, World!")   
    p2 = pd.PathwayData(11, 2, 3, (4, 5), (6, 7), "Hello, World!")   
    p3 = pd.PathwayData(1, 22, 3, (4, 5), (6, 7), "Hello, World!")   
    p4 = pd.PathwayData(1, 2, 33, (4, 5), (6, 7), "Hello, World!")   
    p5 = pd.PathwayData(1, 2, 3, (44, 5), (6, 7), "Hello, World!")   
    p6 = pd.PathwayData(1, 2, 3, (4, 5), (66, 7), "Hello, World!")   
    p7 = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "Hello, World!!")   

    ntools.assert_equal(p0, p1)
    ntools.assert_false(p0 == p2)
    ntools.assert_false(p0 == p3)
    ntools.assert_false(p0 == p4)
    ntools.assert_false(p0 == p5)
    ntools.assert_false(p0 == p6)
    ntools.assert_false(p0 == p7)


def test_PathwayData_str() :

    p = pd.PathwayData(1, 2, 3, (4, 5), (6, 7), "Hello, World!")   
    ntools.assert_equal(str(p),
                        "PathwayData{{'pre': 1, 'syns_per_conn': (6, 7), 'label': 'Hello, World!', 'post': 2, 'v_holding': 3, 'psp': (4, 5)}}")


def test_get_pathway() :
    for l in labels :
        pw = pd.get_pathway(l)
        ntools.assert_equal(pw.label, l)


