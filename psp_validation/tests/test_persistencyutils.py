from sys import path as _path
if '.' not in _path :
    _path.append('.')

from nose import tools as ntools
import os, shutil
from psp_validation import persistencyutils as pu

dir_ = './.test_persistency'
if os.path.exists(dir_):
    shutil.rmtree(dir_)

os.makedirs(dir_)

basename_ = dir_ + '/Foo'

def test_rotated_name_for_new_name() :
    ntools.assert_equal(pu.rotated_name(basename_), basename_)

def test_rotated_name_for_old_name1() :
    open(basename_, 'a').close()
    ntools.assert_equal(pu.rotated_name(basename_), basename_ + '.1')

def test_rotated_name_for_old_name2() :
    open(basename_, 'a').close()
    open(basename_+'.1', 'a').close()
    ntools.assert_equal(pu.rotated_name(basename_), basename_ + '.2')

def test_rotated_name_for_old_name10() :
    open(basename_, 'a').close()
    for i in xrange(1, 10) :
        open(basename_+'.' + str(i), 'a').close()
    ntools.assert_equal(pu.rotated_name(basename_), basename_ + '.10')


def test_jobdirname_is_unique() :

    for i in xrange(10) :
        dir0 = pu.jobdirname()
        dir1 = pu.jobdirname()
        ntools.assert_not_equal(dir0, dir1)


def test_mkjobdir() :

    test_dir = os.path.join(dir_, 'test_mkjobdir')
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    names = [pu.mkjobdir(test_dir) for i in xrange(10)]
    ntools.assert_true(len(names) == 10)
    for n in names :
        ntools.assert_true(os.path.isdir(n))
        
    shutil.rmtree(test_dir)
