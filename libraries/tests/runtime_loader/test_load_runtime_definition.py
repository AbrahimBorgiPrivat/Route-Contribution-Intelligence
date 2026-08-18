import json
import tempfile
from pathlib import Path

import pytest

from libraries.utils.runtime.runtime_loader import load_runtime_definition

def test_load_runtime_definition_ok():
    print("\n[TEST] load_runtime_definition – success case")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        runtime_file = tmpdir / "runner.json"
        data = {
            "pipeline": "test_pipeline",
            "input": {
                "file_path": "dummy.csv"
            },
            "routing": {
                "route_type": "both"
            }
        }
        runtime_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        result = load_runtime_definition(runtime_file)
        assert isinstance(result, dict)
        assert result["pipeline"] == "test_pipeline"
        assert result["input"]["file_path"] == "dummy.csv"
        print("[OK] Runtime definition loaded:")
        print(result)


def test_load_runtime_definition_file_not_found():
    print("\n[TEST] load_runtime_definition – file not found case")
    missing_path = Path("this/path/does/not/exist/runner.json")
    with pytest.raises(FileNotFoundError) as exc:
        load_runtime_definition(missing_path)
    print("[OK] Correctly raised FileNotFoundError")
    print(f"Exception message: {exc.value}")


if __name__ == "__main__":
    test_load_runtime_definition_ok()
    test_load_runtime_definition_file_not_found()
