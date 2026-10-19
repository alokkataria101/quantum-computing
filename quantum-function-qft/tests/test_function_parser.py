"""test_function_parser.py – tests for src/function_parser.py"""
import math, sys, pathlib
import numpy as np
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.function_parser import parse_and_sample, extract_known_components


class TestParseAndSample:
    def test_basic_sine(self):
        s = parse_and_sample("sin(x)", 0.0, math.pi, 64)
        assert s.n_points == 64
        assert abs(float(s.y[0])) < 1e-10          # sin(0) = 0
        assert abs(float(s.y[32]) - 1.0) < 0.03    # sin(pi/2) ≈ 1

    def test_constant_function(self):
        s = parse_and_sample("3.0 + 0*x", 0.0, 1.0, 16)
        np.testing.assert_allclose(s.y, 3.0)

    def test_dc_offset(self):
        s = parse_and_sample("sin(x) + 5", 0.0, 2*math.pi, 64)
        assert abs(s.dc_offset - 5.0) < 0.1

    def test_empty_expr_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_and_sample("", 0, 1, 64)

    def test_bad_domain_raises(self):
        with pytest.raises(ValueError, match="x_end"):
            parse_and_sample("sin(x)", 5.0, 1.0, 64)

    def test_unsafe_import_blocked(self):
        with pytest.raises((ValueError, NameError)):
            parse_and_sample("__import__('os').system('echo hi')", 0, 1, 8)

    def test_dx_correct(self):
        s = parse_and_sample("x", 0.0, 1.0, 11)
        assert abs(s.dx - 0.1) < 1e-10

    def test_n_points_too_small_raises(self):
        with pytest.raises(ValueError):
            parse_and_sample("sin(x)", 0, 1, 1)

    def test_known_components_extracted(self):
        s = parse_and_sample("2*sin(2*pi*3*x) + 1.5*sin(2*pi*7*x + pi/4) + 2",
                             0.0, 1.0, 256)
        freqs = [c.freq_per_unit for c in s.known_components]
        # Should find 3 and 7 cycles/unit
        assert any(abs(f - 3.0) < 0.5 for f in freqs)
        assert any(abs(f - 7.0) < 0.5 for f in freqs)


class TestExtractKnownComponents:
    def test_single_sine(self):
        comps = extract_known_components("3*sin(2*pi*5*x)")
        assert len(comps) >= 1
        freqs = [c.freq_per_unit for c in comps]
        assert any(abs(f - 5.0) < 0.5 for f in freqs)

    def test_negative_sign(self):
        comps = extract_known_components("-sin(2*pi*4*x)")
        assert any(c.amplitude < 0 for c in comps)

    def test_dc_term_not_extracted(self):
        # Pure constant → no sinusoidal components
        comps = extract_known_components("5.0")
        assert len(comps) == 0
