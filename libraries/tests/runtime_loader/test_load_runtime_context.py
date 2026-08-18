import json
import tempfile
from pathlib import Path

import pytest

from libraries.utils.runtime.runtime_loader import load_runtime_context


# ---------------------------------------------------------------------
# Test assets
# ---------------------------------------------------------------------
KPI_REGISTRY_CODE = """
def example_kpi_fn(value):
    return value * 2

KPI_REGISTRY = {
    "example_kpi_fn": example_kpi_fn
}
"""
RUNNER_JSON_WITH_KPI = {
    "pipeline": "test_pipeline",
    "kpi_registry": "kpi_registry.py",
    "kpis": [
        {
            "name": "Example KPI",
            "key": "example",
            "type": "both",
            "fn": "example_kpi_fn"
        }
    ],
    "input": {
        "file_path": "dummy.csv"
    }
}

RUNNER_JSON_NO_KPI = {
    "pipeline": "test_pipeline",
    "input": {
        "file_path": "dummy.csv"
    }
}


def test_load_runtime_context_with_kpi_registry():
    print("\n[TEST] load_runtime_context – with KPI registry")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "runner.json").write_text(
            json.dumps(RUNNER_JSON_WITH_KPI, indent=2),
            encoding="utf-8"
        )
        (tmpdir / "kpi_registry.py").write_text(
            KPI_REGISTRY_CODE,
            encoding="utf-8"
        )
        ctx = load_runtime_context(tmpdir)
        assert "config" in ctx
        assert "kpi_mapping" in ctx
        config = ctx["config"]
        kpi_mapping = ctx["kpi_mapping"]
        print("[INFO] Loaded config:")
        print(config)
        print("[INFO] Resolved KPI mapping:")
        print(kpi_mapping)
        assert config["pipeline"] == "test_pipeline"
        assert config["input"]["file_path"] == "dummy.csv"
        assert isinstance(kpi_mapping, list)
        assert len(kpi_mapping) == 1
        kpi = kpi_mapping[0]
        assert kpi["name"] == "Example KPI"
        assert kpi["key"] == "example"
        assert kpi["type"] == "both"
        fn = kpi["val"]
        assert callable(fn)
        result = fn(3)
        assert result == 6
        print("[OK] KPI mapping resolved correctly")


def test_load_runtime_context_without_kpi_registry():
    print("\n[TEST] load_runtime_context – without KPI registry")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "runner.json").write_text(
            json.dumps(RUNNER_JSON_NO_KPI, indent=2),
            encoding="utf-8"
        )
        ctx = load_runtime_context(tmpdir)
        print("[INFO] Loaded context:")
        print(ctx)
        assert "config" in ctx
        assert "kpi_mapping" not in ctx
        assert ctx["config"]["pipeline"] == "test_pipeline"
        print("[OK] Runtime context loaded without KPI registry")

def test_load_runtime_context_missing_kpi_registry_file():
    print("\n[TEST] load_runtime_context – missing KPI registry file")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "runner.json").write_text(
            json.dumps(RUNNER_JSON_WITH_KPI, indent=2),
            encoding="utf-8"
        )
        with pytest.raises(FileNotFoundError) as exc:
            load_runtime_context(tmpdir)
        print("[OK] Correctly raised FileNotFoundError")
        print(f"Exception message: {exc.value}")


if __name__ == "__main__":
    test_load_runtime_context_with_kpi_registry()
    test_load_runtime_context_without_kpi_registry()
    test_load_runtime_context_missing_kpi_registry_file()
