import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from libraries.utils.pipelines.b_route_preparation_layer.pipeline_existing_route_guard import (
    route_output_exists,
)


def test_route_output_exists_false_when_target_folder_is_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert route_output_exists(
            save_root=tmpdir,
            label_name="LabelA",
            route_id=37000001,
            apr_label="APR_A",
            week_label="Week_12",
        ) is False


def test_route_output_exists_true_when_target_folder_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = (
            Path(tmpdir)
            / "LabelA"
            / "37000001"
            / "APR_A"
            / "Week_12"
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        assert route_output_exists(
            save_root=tmpdir,
            label_name="LabelA",
            route_id=37000001,
            apr_label="APR_A",
            week_label="Week_12",
        ) is True


def test_route_output_exists_false_for_other_folder_combination():
    with tempfile.TemporaryDirectory() as tmpdir:
        existing_dir = (
            Path(tmpdir)
            / "LabelA"
            / "37000001"
            / "APR_A"
            / "Week_12"
        )
        existing_dir.mkdir(parents=True, exist_ok=True)

        assert route_output_exists(
            save_root=Path(tmpdir),
            label_name="LabelA",
            route_id=37000001,
            apr_label="APR_A",
            week_label="Week_13",
        ) is False


if __name__ == "__main__":
    test_route_output_exists_false_when_target_folder_is_missing()
    test_route_output_exists_true_when_target_folder_exists()
    test_route_output_exists_false_for_other_folder_combination()
