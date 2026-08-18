import pytest
from libraries.utils.runtime.runtime_loader import resolve_kpi_mapping

# ---------------------------------------------------------------------
# Example KPI registry and mappings
# ---------------------------------------------------------------------
def example_kpi_fn(value):
    return value * 2
KPI_REGISTRY = {
    "example_kpi_fn": example_kpi_fn
}
KPI_MAPPING_VALID = [
    {
        "name": "Example KPI",
        "key": "example",
        "type": "both",              
        "fn": "example_kpi_fn",
    }
]
KPI_MAPPING_MISSING_FN = [
    {
        "name": "Broken KPI",
        "key": "broken",
        "type": "both",             
        "fn": "missing_function",
    }
]

def test_resolve_kpi_mapping_ok():
    print("\n[TEST] resolve_kpi_mapping – success case")
    resolved = resolve_kpi_mapping(
        kpi_defs=KPI_MAPPING_VALID,
        registry=KPI_REGISTRY,
    )
    assert isinstance(resolved, list)
    assert len(resolved) == 1
    kpi = resolved[0]
    assert kpi["name"] == "Example KPI"
    assert kpi["key"] == "example"
    fn = kpi["val"]
    assert callable(fn)
    result = fn(3)
    assert result == 6
    print("[OK] Resolved KPI mapping:")
    print(resolved)


def test_resolve_kpi_mapping_missing_function():
    print("\n[TEST] resolve_kpi_mapping – missing function case")
    with pytest.raises(ValueError) as exc:
        resolve_kpi_mapping(
            kpi_defs=KPI_MAPPING_MISSING_FN,
            registry=KPI_REGISTRY,
        )
    print("[OK] Correctly raised ValueError")
    print(f"Exception message: {exc.value}")


def test_resolve_kpi_mapping_empty():
    print("\n[TEST] resolve_kpi_mapping – empty mapping")
    resolved = resolve_kpi_mapping(
        kpi_defs=[],
        registry=KPI_REGISTRY,
    )
    assert resolved == []
    print("[OK] Empty KPI mapping resolved correctly")

if __name__ == "__main__":
    test_resolve_kpi_mapping_ok()
    test_resolve_kpi_mapping_missing_function()
    test_resolve_kpi_mapping_empty()
