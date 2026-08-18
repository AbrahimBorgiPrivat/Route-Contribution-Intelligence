import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import libraries.utils.pipelines.pipelines.application.v2.run_route_data_pipeline as pipeline_module
from libraries.utils.pipelines.pipelines.application.v2.run_route_data_pipeline import (
    run_route_data_pipeline_v2,
)
from libraries.tests._utils.skip_if_service_down import skip_if_service_unavailable


def test_run_route_data_pipeline_application_v2():
    skip_if_service_unavailable(
        url="http://localhost:5000",
        reason="Local OSRM service not running",
    )
    skip_if_service_unavailable(
        url="http://localhost:5010",
        reason="Local OSM SNAPPER service not running",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        default_runner = {
            "input": {
                "file_path": "libraries/tests/_test_dataset/test_data.csv",
                "file_seperator": ";",
            },
            "output": {
                "save_dir": tmpdir,
            },
            "routing": {
                "route_type": "both",
                "start_routes": None,
                "max_routes": 2,
            },
            "algorithm": {
                "E": 5.0,
                "z": 0.0,
                "k_max": 8,
                "k_all": 1,
                "B": 4,
                "solver_tsp": "ortools",
                "solver_hpp": "ortools",
                "deterministic_tsp": True,
                "deterministic_hpp": True,
                "precheck": True,
                "ortools_time_limit": 2,
                "initial_point_method": {"method": "GREEDY_DNN"},
                "type1_methods": ["A", "B"],
                "type2_methods": ["A", "B"],
                "A_kwargs": {"method": "kneedle"},
                "B_kwargs": {"L_max": 8},
                "U_kwargs": {},
            },
            "geometry": {
                "allowed_highways": [
                    "primary",
                    "secondary",
                    "tertiary",
                    "residential",
                    "living_street",
                ],
                "chunk_size_osm": 2,
                "chunk_size_osrm": 50,
                "use_rotated_side": True,
                "offset_m": 2.5,
                "entry_angle_deg": -60.0,
                "exit_angle_deg": 60.0,
                "unit_entry_exit_strategy": "OSRM_CLOSEST",
            },
            "mappings": {
                "col_map": {
                    "route_id": {"name": "id"},
                    "lon": {"name": "vejx"},
                    "lat": {"name": "vejy"},
                    "line_nr": {"name": "linienr"},
                    "transform": {
                        "convert_from": "EPSG:25832",
                        "convert_to": "EPSG:4326",
                    },
                    "problem_type": {
                        "name": "beregning",
                        "OUT:TSP": [0, 1, 2],
                    },
                }
            },
        }
        label_list = [
            {
                "c_cache_config": {
                    "label": "Ustruktureret metode - Alle Adresser",
                    "base_path": tmpdir,
                    "enabled": True,
                },
                "label_explanation": "Korteste rute mellem alle adresser uden sektionsregler.",
                "overwrite": {
                    "mappings": {
                        "col_map": {
                            "problem_type": {
                                "name": "beregning",
                                "HPP": [1],
                                "TSP": [0, 2],
                            }
                        }
                    }
                },
            },
            {
                "c_cache_config": {
                    "label": "Struktureret metode - Omsætende Adresser",
                    "base_path": tmpdir,
                    "enabled": False,
                },
                "label_explanation": "Korteste rute mellem omsættende adresser med sektionsregler.",
                "overwrite": {
                    "mappings": {
                        "col_map": {
                            "problem_type": {
                                "name": "beregning",
                                "HPP": [1],
                                "OUT:TSP": [0, 2],
                            }
                        }
                    }
                },
            },
        ]
        APR_profiles = [
            {
                "APR Label": "Standard profil",
                "APR_explanation": "Standard APR-profil til test.",
                "APR": {
                    "foot": {"distance": 0.03},
                    "bike": {"distance": 0.01},
                    "bicycle": {"distance": 0.01},
                    "car": {"duration": 0.0555556},
                },
            },
            {
                "APR Label": "Høj profil",
                "APR_explanation": "Høj APR-profil til test.",
                "APR": {
                    "foot": {"distance": 0.6},
                    "bike": {"distance": 0.2},
                    "bicycle": {"distance": 0.2},
                    "car": {"duration": 0.2},
                },
            },
        ]
        revenue_list = [
            {
                "revenue label": "Gns. Omsætning",
                "revenue_explanation": "Gennemsnitlig omsætning på tværs af testuger.",
                "revenue": {
                    "path_revenue": "libraries/tests/_test_dataset/test_revenue_data.csv",
                    "sep": ";",
                    "join_fields": {
                        "kommune": "kommune",
                        "vejnr": "vejnr",
                        "husnr": "husnr",
                        "husbog": "husbog",
                    },
                    "rev_fields": [
                        "week_2536",
                        "week_2537",
                        "week_2538",
                        "week_2539",
                    ],
                    "rev_formula": "AVG",
                    "rev_include_all_addresses": True,
                },
            },
            {
                "revenue label": "Uge 36",
                "revenue_explanation": "Omsætning baseret på testdata for uge 36.",
                "revenue": {
                    "path_revenue": "libraries/tests/_test_dataset/test_revenue_data.csv",
                    "sep": ";",
                    "join_fields": {
                        "kommune": "kommune",
                        "vejnr": "vejnr",
                        "husnr": "husnr",
                        "husbog": "husbog",
                    },
                    "rev_fields": ["week_2536"],
                    "rev_formula": "SUM",
                    "rev_include_all_addresses": True,
                },
            },
        ]
        run_route_data_pipeline_v2(
            file_path=default_runner["input"]["file_path"],
            file_seperator=default_runner["input"]["file_seperator"],
            route_type=default_runner["routing"]["route_type"],
            start_routes=default_runner["routing"]["start_routes"],
            max_routes=default_runner["routing"]["max_routes"],
            E=default_runner["algorithm"]["E"],
            z=default_runner["algorithm"]["z"],
            k_max=default_runner["algorithm"]["k_max"],
            k_all=default_runner["algorithm"]["k_all"],
            B=default_runner["algorithm"]["B"],
            solver_tsp=default_runner["algorithm"]["solver_tsp"],
            solver_hpp=default_runner["algorithm"]["solver_hpp"],
            deterministic_tsp=default_runner["algorithm"]["deterministic_tsp"],
            deterministic_hpp=default_runner["algorithm"]["deterministic_hpp"],
            precheck=default_runner["algorithm"]["precheck"],
            ortools_time_limit=default_runner["algorithm"]["ortools_time_limit"],
            initial_point_method=default_runner["algorithm"]["initial_point_method"],
            type1_methods=default_runner["algorithm"]["type1_methods"],
            type2_methods=default_runner["algorithm"]["type2_methods"],
            A_kwargs=default_runner["algorithm"]["A_kwargs"],
            B_kwargs=default_runner["algorithm"]["B_kwargs"],
            U_kwargs=default_runner["algorithm"]["U_kwargs"],
            allowed_highways=default_runner["geometry"]["allowed_highways"],
            chunk_size_osm=default_runner["geometry"]["chunk_size_osm"],
            chunk_size_osrm=default_runner["geometry"]["chunk_size_osrm"],
            use_rotated_side=default_runner["geometry"]["use_rotated_side"],
            offset_m=default_runner["geometry"]["offset_m"],
            entry_angle_deg=default_runner["geometry"]["entry_angle_deg"],
            exit_angle_deg=default_runner["geometry"]["exit_angle_deg"],
            unit_entry_exit_strategy=default_runner["geometry"]["unit_entry_exit_strategy"],
            col_map=default_runner["mappings"]["col_map"],
            label_list=label_list,
            APR_profiles=APR_profiles,
            revenue_list=revenue_list,
            save_root=default_runner["output"]["save_dir"],
        )
        base_dir = Path(tmpdir)
        for label_cfg in label_list:
            label_name = label_cfg["c_cache_config"]["label"]
            label_path = base_dir / label_name
            assert label_path.exists()
            for route_dir in label_path.iterdir():
                assert route_dir.is_dir()
                for apr_dir in route_dir.iterdir():
                    assert apr_dir.name in [p["APR Label"] for p in APR_profiles]
                    for week_dir in apr_dir.iterdir():
                        assert week_dir.name in [r["revenue label"] for r in revenue_list]
                        assert week_dir.name in [r["revenue label"] for r in revenue_list]
        registry_path = base_dir / "registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        expected_labels = len(label_list)
        expected_routes = 2  
        expected_apr = len(APR_profiles)
        expected_weeks = len(revenue_list)
        expected_total = (
            expected_labels
            * expected_routes
            * expected_apr
            * expected_weeks
        )
        assert len(registry) == expected_total
        sample = registry[0]
        assert "label" in sample
        assert "route_id" in sample
        assert "APR_profile" in sample
        assert "Week_Profile" in sample
        assert "route_json" in sample
        route_json_path = base_dir / sample["route_json"]
        assert route_json_path.exists()
        metadata_path = base_dir / "scenario_metadata.json"
        assert metadata_path.exists()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        from pprint import pprint
        assert metadata["labels"] == {'Struktureret metode - Omsætende Adresser': 'Korteste rute mellem omsættende adresser med sektionsregler.',
            'Ustruktureret metode - Alle Adresser': 'Korteste rute mellem alle adresser uden sektionsregler.'}
        assert metadata["APR_profiles"] == {'Høj profil': 'Høj APR-profil til test.',
                                            'Standard profil': 'Standard APR-profil til test.'}
        assert metadata["week_profiles"] == {
            "Gns. Omsætning": "Gennemsnitlig omsætning på tværs af testuger.",
            "Uge 36": "Omsætning baseret på testdata for uge 36.",
        }


def test_run_route_data_pipeline_application_v2_skips_existing_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        label_name = "Existing Label"
        route_id = 37000001
        apr_label = "APR Profile"
        week_label = "Week 12"
        existing_dir = (
            Path(tmpdir)
            / label_name
            / str(route_id)
            / apr_label
            / week_label
        )
        existing_dir.mkdir(parents=True, exist_ok=True)

        ctx = SimpleNamespace(
            route_ids=[route_id],
            df=None,
            APR={"foot": {"distance": 0.1}},
            strict_values=[True, False],
        )

        with (
            patch.object(
                pipeline_module,
                "init_pipeline_context",
                return_value=ctx,
            ) as mock_init_context,
            patch.object(
                pipeline_module,
                "prepare_route_and_matrices",
            ) as mock_prepare_route,
            patch.object(
                pipeline_module,
                "run_outlier_detection_for_route_v2",
            ) as mock_run_detection,
            patch.object(
                pipeline_module,
                "build_single_route_data",
            ) as mock_build_route_data,
        ):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                run_route_data_pipeline_v2(
                    file_path="unused.csv",
                    col_map={"route_id": {"name": "route_id"}},
                    label_list=[
                        {
                            "c_cache_config": {
                                "label": label_name,
                            }
                        }
                    ],
                    APR_profiles=[
                        {
                            "APR Label": apr_label,
                            "APR": {"foot": {"distance": 0.1}},
                        }
                    ],
                    revenue_list=[
                        {
                            "revenue label": week_label,
                        }
                    ],
                    save_root=tmpdir,
                )

        mock_init_context.assert_called_once()
        mock_prepare_route.assert_not_called()
        mock_run_detection.assert_not_called()
        mock_build_route_data.assert_not_called()

        output = stdout.getvalue()
        assert f"Starting Route {route_id}" in output
        assert f"Skipping Route {route_id}" in output

        registry_path = Path(tmpdir) / "registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        assert registry == []


if __name__ == "__main__":
    test_run_route_data_pipeline_application_v2()
    test_run_route_data_pipeline_application_v2_skips_existing_output()

