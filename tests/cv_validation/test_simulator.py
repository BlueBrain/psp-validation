import logging
from unittest.mock import patch

import pytest
from numpy.testing import assert_array_equal

import psp_validation.cv_validation.simulator as test_module
from psp_validation import PSPError


@pytest.mark.parametrize("protocol", [{}, {"hold_I": 666.666, "hold_V": 666.666}])
def test_resolve_holding_current_and_voltage_error(protocol):
    with pytest.raises(PSPError, match="Either 'hold_V' or 'hold_I' should be specified"):
        test_module.resolve_holding_current_and_voltage(
            protocol, clamp=None, post_gid=None, simulation_config=None, post_ttx=None
        )


@pytest.mark.parametrize(
    ("protocol", "clamp", "expected"),
    [
        ({"hold_I": 666.666}, "current", [666.666, None]),
        ({"hold_V": 666.666}, "current", ["mock_current", 666.666]),
        ({"hold_V": 666.666}, "voltage", [None, 666.666]),
    ],
)
@patch.object(test_module, "_resolve_holding_current")
def test_resolve_current_and_voltage(mock_resolve_current, protocol, clamp, expected):
    mock_resolve_current.return_value = "mock_current"
    post_gid = simulation_config = post_ttx = None

    assert_array_equal(
        test_module.resolve_holding_current_and_voltage(
            protocol, clamp, post_gid, simulation_config, post_ttx=post_ttx
        ),
        expected,
    )

    if clamp == "current" and "hold_I" not in protocol:
        mock_resolve_current.assert_called_once_with(
            protocol["hold_V"], post_gid, simulation_config, post_ttx
        )
    else:
        mock_resolve_current.assert_not_called()


@patch.object(test_module, "get_holding_current")
def test__resolve_holding_current(mock_get_holding_current, caplog):
    mock_get_holding_current.return_value = "mock_current"
    post_gid = simulation_config = post_ttx = None

    hold_v = None
    with caplog.at_level(logging.WARNING):
        res = test_module._resolve_holding_current(hold_v, post_gid, simulation_config, post_ttx)
        assert res == 0
        assert "'hold_V' is None. 'hold_I' will be set to 0" in caplog.text
        mock_get_holding_current.assert_not_called()

    hold_v = 10
    res = test_module._resolve_holding_current(hold_v, post_gid, simulation_config, post_ttx)
    mock_get_holding_current.assert_called_once_with(
        log_level=100,
        hold_V=hold_v,
        post_gid=post_gid,
        sonata_simulation_config=simulation_config,
        post_ttx=post_ttx,
    )
    assert res == "mock_current"
