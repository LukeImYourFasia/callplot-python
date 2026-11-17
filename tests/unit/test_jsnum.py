# Unit tests for jsnum helpers (DESIGN-PYTHON.md section 3.9, Version 2).
# The JS number rows were confirmed on Node 24 (2026-11-15).

import re

import pytest

from callplot.errors import CallplotError
from callplot.jsnum import js_num, js_round, js_to_fixed


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(75.0, "75"), (116.5, "116.5"), (3, "3"), (0.0, "0"), (-0.0, "0")],
)
def test_js_num__template_literal_printing(value, want):
    assert js_num(value) == want


@pytest.mark.unit
def test_js_num__bool__raises_callplot_error():
    with pytest.raises(CallplotError, match=re.escape("jsNum: not a number")):
        js_num(True)


# trap 22: the 5 rows of DESIGN-PYTHON.md section 3.9
@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [
        (50.0, "50"),
        (-0.0, "0"),
        (1e16, "10000000000000000"),
        (2.5e-5, "0.000025"),
        (0.1 + 0.2, "0.30000000000000004"),
    ],
)
def test_js_num__trap_22__section_3_9_rows(value, want):
    assert js_num(value) == want


# trap 23: the 4 rows of section 3.9 for js_to_fixed
@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "digits", "want"),
    [(0.25, 1, "0.3"), (2.5, 0, "3"), (1.005, 2, "1.00"), (-0.25, 1, "-0.3")],
)
def test_js_to_fixed__trap_23__section_3_9_rows(value, digits, want):
    assert js_to_fixed(value, digits) == want


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(2.5, 3), (-2.5, -2), (-0.5, 0), (0.5, 1), (0.4999999999, 0), (1.4999, 1)],
)
def test_js_round__half_up_to_plus_infinity(value, want):
    assert js_round(value) == want


@pytest.mark.unit
def test_js_round__differs_from_python_round_on_halves():
    assert round(2.5) == 2  # banker's rounding (DESIGN 3.4 trap row)
    assert js_round(2.5) == 3  # Math.round is half toward +Infinity
    assert round(0.5) == 0
    assert js_round(0.5) == 1


# trap 24: the 3 rows of section 3.9 for js_round
@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(-2.5, -2), (2.5, 3), (0.49999999999999994, 0)],
)
def test_js_round__trap_24__section_3_9_rows(value, want):
    assert js_round(value) == want
