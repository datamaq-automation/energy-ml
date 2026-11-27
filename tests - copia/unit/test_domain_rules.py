"""tests/unit/test_domain_rules.py — Ejemplo de prueba unitaria de Dominio Puro (Zero External Dependencies)."""

from __future__ import annotations

import pytest


class SampleValueObject:
    def __init__(self, value: str) -> None:
        if not value or len(value.strip()) == 0:
            raise ValueError("El valor no puede estar vacío.")
        self.value = value.strip()


def test_sample_value_object_success() -> None:
    vo = SampleValueObject("  test-value  ")
    assert vo.value == "test-value"


def test_sample_value_object_empty_fails() -> None:
    with pytest.raises(ValueError, match="no puede estar vacío"):
        SampleValueObject("   ")
