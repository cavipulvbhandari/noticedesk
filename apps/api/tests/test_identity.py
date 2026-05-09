"""Unit tests for the identity utility module.

These run without a database. The async resolver functions are exercised
in tests/integration/ once a Postgres instance is available.
"""

from __future__ import annotations

import pytest

from app.services.identity import (
    extract_pan_from_gstin,
    extract_state_code_from_gstin,
    get_state_name_from_code,
    reconcile_pan_gstin,
    validate_gstin_format,
    validate_pan_format,
)


class TestValidatePanFormat:
    @pytest.mark.parametrize(
        "pan",
        [
            "AAACX1234F",
            "ABCDE1234F",
            "ZZZZZ9999Z",
        ],
    )
    def test_valid(self, pan: str) -> None:
        assert validate_pan_format(pan) is True

    @pytest.mark.parametrize(
        "pan",
        [
            "ABCDE1234X9",  # too long
            "ABCDE1234",    # missing trailing letter
            "abcde1234x",   # lowercase
            "12345AAAAA",   # digits in alpha positions
            "AAAAA1234X1",  # 11 chars
            "",
            "AAAAA12345",   # last char must be a letter
        ],
    )
    def test_invalid(self, pan: str) -> None:
        assert validate_pan_format(pan) is False

    def test_non_string(self) -> None:
        assert validate_pan_format(None) is False  # type: ignore[arg-type]
        assert validate_pan_format(12345) is False  # type: ignore[arg-type]


class TestValidateGstinFormat:
    @pytest.mark.parametrize(
        "gstin",
        [
            "27AAACX1234F1Z5",
            "29AAACX1234F1Z9",
            "24AAACX1234F1Z3",
            "07AAACX1234FAZK",  # entity number can be A-Z; checksum can be alphanumeric
        ],
    )
    def test_valid(self, gstin: str) -> None:
        assert validate_gstin_format(gstin) is True

    @pytest.mark.parametrize(
        "gstin",
        [
            "27AAACX1234F1Z",     # 14 chars
            "27AAACX1234F1Z55",   # 16 chars
            "27AAACX1234F1A5",    # position 14 must be 'Z'
            "27aaacx1234f1z5",    # lowercase
            "XXAACX1234F1Z5",     # state code letters
            "",
        ],
    )
    def test_invalid(self, gstin: str) -> None:
        assert validate_gstin_format(gstin) is False


class TestExtractPanFromGstin:
    def test_returns_pan(self) -> None:
        assert extract_pan_from_gstin("27AAACX1234F1Z5") == "AAACX1234F"

    def test_state_code(self) -> None:
        assert extract_state_code_from_gstin("27AAACX1234F1Z5") == "27"
        assert extract_state_code_from_gstin("29AAACX1234F1Z9") == "29"

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            extract_pan_from_gstin("not-a-gstin")
        with pytest.raises(ValueError):
            extract_state_code_from_gstin("nope")


class TestReconcilePanGstin:
    def test_match(self) -> None:
        assert reconcile_pan_gstin("AAACX1234F", "27AAACX1234F1Z5") is True

    def test_match_different_state(self) -> None:
        assert reconcile_pan_gstin("AAACX1234F", "29AAACX1234F1Z9") is True

    def test_mismatch(self) -> None:
        assert reconcile_pan_gstin("AAACX1234F", "27ZZZZZ1234F1Z5") is False

    def test_brief_acceptance_match(self) -> None:
        # The Sprint 1 brief calls out this exact assertion.
        assert reconcile_pan_gstin("AAACA9876B", "27AAACA9876B1ZK") is True

    def test_brief_acceptance_mismatch(self) -> None:
        # Acme PAN against Sunteck's GSTIN — must not reconcile.
        assert reconcile_pan_gstin("AAACA9876B", "27AABCS5678C1Z7") is False

    def test_invalid_pan(self) -> None:
        assert reconcile_pan_gstin("not-a-pan", "27AAACX1234F1Z5") is False

    def test_invalid_gstin(self) -> None:
        assert reconcile_pan_gstin("AAACX1234F", "not-a-gstin") is False


class TestGetStateNameFromCode:
    @pytest.mark.parametrize(
        "code,name",
        [
            ("27", "Maharashtra"),
            ("29", "Karnataka"),
            ("24", "Gujarat"),
            ("07", "Delhi"),
            ("33", "Tamil Nadu"),
        ],
    )
    def test_known(self, code: str, name: str) -> None:
        assert get_state_name_from_code(code) == name

    @pytest.mark.parametrize("code", ["00", "98", "abc", "", "1", "270"])
    def test_unknown_or_malformed(self, code: str) -> None:
        assert get_state_name_from_code(code) is None

    def test_non_string(self) -> None:
        assert get_state_name_from_code(None) is None  # type: ignore[arg-type]
        assert get_state_name_from_code(27) is None  # type: ignore[arg-type]
