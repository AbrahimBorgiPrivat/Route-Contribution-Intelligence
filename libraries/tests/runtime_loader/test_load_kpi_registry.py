import tempfile
from pathlib import Path

import pytest

from libraries.utils.runtime.runtime_loader import load_kpi_registry

REGISTRY_CODE = """
def example_kpi_fn(x):
    return x * 2

KPI_REGISTRY = {
    "example_kpi_fn": example_kpi_fn
}
"""

REGISTRY_CODE_MISSING_KPI_REGISTRY = """
def some_function(x):
    return x
"""

def test_load_kpi_registry_ok():
    print("\n[TEST] load_kpi_registry – success case")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        registry_file = tmpdir / "kpi_registry.py"
        registry_code = REGISTRY_CODE
        registry_file.write_text(registry_code, encoding="utf-8")
        registry = load_kpi_registry(registry_file)
        assert isinstance(registry, dict)
        assert "example_kpi_fn" in registry
        assert callable(registry["example_kpi_fn"])
        fn = registry["example_kpi_fn"]
        result = fn(3)
        assert result == 6
        print("[OK] KPI registry loaded:")
        print(registry)


def test_load_kpi_registry_file_not_found():
    print("\n[TEST] load_kpi_registry – file not found case")
    missing_path = Path("this/path/does/not/exist/kpi_registry.py")
    with pytest.raises(FileNotFoundError) as exc:
        load_kpi_registry(missing_path)
    print("[OK] Correctly raised FileNotFoundError")
    print(f"Exception message: {exc.value}")


def test_load_kpi_registry_missing_KPI_REGISTRY():
    print("\n[TEST] load_kpi_registry – missing KPI_REGISTRY case")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        registry_file = tmpdir / "kpi_registry.py"
        registry_code = REGISTRY_CODE_MISSING_KPI_REGISTRY
        registry_file.write_text(registry_code, encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            load_kpi_registry(registry_file)
        print("[OK] Correctly raised ValueError")
        print(f"Exception message: {exc.value}")

if __name__ == "__main__":
    test_load_kpi_registry_ok()
    test_load_kpi_registry_file_not_found()
    test_load_kpi_registry_missing_KPI_REGISTRY()
