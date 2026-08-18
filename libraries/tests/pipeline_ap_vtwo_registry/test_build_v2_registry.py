import json
import tempfile
from pathlib import Path

from libraries.utils.pipelines.d_application_layer.application.v2.pipeline_ap_vtwo_registry import build_v2_registry

def _write_minimal_v2_structure(base_dir: Path):
    week_dir = (
        base_dir
        / "Label"
        / "37000001"
        / "APR"
        / "Week"
    )
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / "37000001.json").write_text(
        json.dumps({"route_id": "37000001"})
    )
    (week_dir / "37000001_markers.geojson").write_text("{}")
    (week_dir / "37000001_route.geojson").write_text("{}")


def test_build_v2_registry_pipeline_wrapper():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        _write_minimal_v2_structure(base_dir)
        registry_path = build_v2_registry(
            save_dir=str(base_dir),
            label_list=[
                {
                    "c_cache_config": {"label": "Label"},
                    "label_explanation": "Forklaring af label.",
                }
            ],
            APR_profiles=[
                {
                    "APR Label": "APR",
                    "APR_explanation": "Forklaring af APR-profil.",
                }
            ],
            revenue_list=[
                {
                    "revenue label": "Week",
                    "revenue_explanation": "Forklaring af ugeprofil.",
                }
            ],
        )
        assert Path(registry_path).exists()
        registry = json.loads(open(registry_path, encoding="utf-8").read())
        assert len(registry) == 1
        entry = registry[0]
        assert entry["label"] == "Label"
        assert entry["route_id"] == "37000001"
        assert entry["APR_profile"] == "APR"
        assert entry["Week_Profile"] == "Week"
        assert entry["route_json"] == (
            "Label/37000001/APR/Week/37000001.json"
        )
        metadata_path = base_dir / "scenario_metadata.json"
        assert metadata_path.exists()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["labels"]["Label"] == "Forklaring af label."
        assert metadata["APR_profiles"]["APR"] == "Forklaring af APR-profil."
        assert metadata["week_profiles"]["Week"] == "Forklaring af ugeprofil."

if __name__ == "__main__":
    test_build_v2_registry_pipeline_wrapper()
