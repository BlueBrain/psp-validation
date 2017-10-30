import bluepy
import bglibpy

from nose import tools as nt

bp_config = "psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling"

def test_instantiate_sim() :
    """
    Test whether bglibpy.ssim.SSim can be instantiated
    """
    sim = bglibpy.ssim.SSim(bp_config)

def test_instantiate_gids_does_not_raise() :
    """
    Test whether SSim instance's gids can be instantiated.
    Catch all exceptions and nose.tools.assert to trigger a
    test failure instead of an error.
    """
    sim = bglibpy.ssim.SSim(bp_config)
    try :
        sim.instantiate_gids([5], synapse_detail=0)
    except :
        nt.assert_true(False)

