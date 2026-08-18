import copy

from libraries.utils.pipelines.a_context_layer.pipeline_build_config import (
    _build_v2_config,
)


def test_build_v2_config_precedence():

    default_runner = {
        "algorithm": {
            "APR": 0.03,
            "E": 5.0,
        },
        "mappings": {
            "col_map": {
                "problem_type": {"name": "beregning", "TSP": [1]},
            }
        },
    }
    label_cfg = {
        "rev_include_all_addresses": False,
        "overwrite": {
            "mappings": {
                "col_map": {
                    "problem_type": {"name": "beregning", "HPP": [1]}
                }
            }
        },
    }
    apr_cfg = {
        "APR Label": "TestAPR",
        "APR": {"foot": {"distance": 0.6}},
    }
    revenue_cfg = {
        "revenue label": "TestRevenue",
        "revenue": {
            "path_revenue": "dummy.csv",
            "rev_include_all_addresses": True
        }
    }
    default_runner_copy = copy.deepcopy(default_runner)
    result = _build_v2_config(
        default_runner=default_runner,
        label_cfg=label_cfg,
        apr_cfg=apr_cfg,
        revenue_cfg=revenue_cfg,
    )

    # --------------------------------------------------
    # 1. default_runner should not be mutated
    # --------------------------------------------------
    assert default_runner == default_runner_copy

    # --------------------------------------------------
    # 2. APR override applied
    # --------------------------------------------------
    assert result["algorithm"]["APR"] == {"foot": {"distance": 0.6}}

    # --------------------------------------------------
    # 3. Revenue injected
    # --------------------------------------------------
    assert result["mappings"]["col_map"]["revenue"]["path_revenue"] == "dummy.csv"

    # --------------------------------------------------
    # 4. Label overwrite has highest priority
    # --------------------------------------------------
    assert result["mappings"]["col_map"]["problem_type"] == {
        "name": "beregning",
        "HPP": [1],
    }

    # --------------------------------------------------
    # 5. Label-level rev_include_all_addresses overrides revenue level
    # --------------------------------------------------
    assert (
        result["mappings"]["col_map"]["revenue"]["rev_include_all_addresses"]
        is False
    )


def test_build_v2_config_no_revenue():

    default_runner = {
        "algorithm": {"APR": 0.03},
        "mappings": {"col_map": {}},
    }

    label_cfg = {"overwrite": {}}

    apr_cfg = {
        "APR Label": "TestAPR",
        "APR": {"foot": {"distance": 0.03}},
    }

    revenue_cfg = {
        "revenue label": "None",
        "revenue": None
    }

    result = _build_v2_config(
        default_runner=default_runner,
        label_cfg=label_cfg,
        apr_cfg=apr_cfg,
        revenue_cfg=revenue_cfg,
    )

    assert result["algorithm"]["APR"] == {"foot": {"distance": 0.03}}
    assert "revenue" not in result["mappings"]["col_map"]

def test_build_v2_config_rev_flag_behavior():

    # Base runner with revenue already defined
    default_runner = {
        "input": {
        "file_path": "test.csv",
        "file_seperator": ";"
        },
        "output": {
        "save_dir": "./test"
        },
        "routing": {
        "route_type": "both",
        "start_routes": None,
        "max_routes": 2
        },
        "algorithm": {
        "E": 5.0,
        "z": 0.0,
        "k_max": 25,
        "k_all": 1,
        "B": 10,
        "solver_tsp": "ortools",
        "solver_hpp": "ortools",
        "deterministic_tsp": True,
        "deterministic_hpp": True,
        "precheck": True,
        "ortools_time_limit": 2,
        "initial_point_method": { "method": "GREEDY_DNN" },
        "type1_methods": ["A", "B", "U"],
        "type2_methods": ["A", "B", "U"],
        "A_kwargs": None,
        "B_kwargs": None,
        "U_kwargs": {
            "max_combination_size": 2,
            "max_union_size": 10
        }
        },
        "geometry": {
        "allowed_highways": [
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "living_street"
        ],
        "chunk_size_osm": 2,
        "chunk_size_osrm": 50,
        "use_rotated_side": True,
        "offset_m": 2.5,
        "entry_angle_deg": -60.0,
        "exit_angle_deg": 60.0,
        "unit_entry_exit_strategy": "OSRM_CLOSEST"
        },
        "mappings": {
        "col_map": {
            "route_id": { "name": "id" },
            "lon": { "name": "vejx" },
            "lat": { "name": "vejy" },
            "line_nr": { "name": "linienr" },
            "transform": {
            "convert_from": "EPSG:25832",
            "convert_to": "EPSG:4326"
            }
        }
        },
        "flags": {
        "use_data": True,
        "index_filename": "routes_index.json"
        }
    }

    # Label forces rev_include_all_addresses = False
    label_cfg = {
      "c_cache_config": {
        "label": "Struktureret med omsættende adresser",
        "base_path": "./views/application/v2/data",
        "enabled": True
      },
      "rev_include_all_addresses": False,
      "overwrite": {
        "mappings": {
          "col_map": {
            "problem_type": {
              "name": "beregning",
              "HPP": [1],
              "OUT:TSP": [0, 2]
            }
          }
        }
      }
    }

    apr_cfg = {
      "APR Label": "U18 Omdeler",
      "APR": {
              "foot": {
                "distance": 0.02009
              },
              "bike": {
                "distance": 0.00624
              },
              "bicycle": {
                "distance": 0.00624
              },
              "car": {
                "duration": 0.03944
              }
            }
    }

    revenue_cfg = {
      "revenue label": "Gns. Oms",
      "revenue": {
        "path_revenue": "override.csv",
        "sep": ";",
        "join_fields": {
          "kommune": "kommune",
          "vejnr": "vejnr",
          "husnr": "husnr",
          "husbog": "husbog"
        },
        "rev_fields": [
          "week_2536",
          "week_2537",
          "week_2538",
          "week_2539"
        ],
        "rev_formula": "AVG",
        "rev_include_all_addresses": True
      }
    }

    result = _build_v2_config(
        default_runner=default_runner,
        label_cfg=label_cfg,
        apr_cfg=apr_cfg,
        revenue_cfg=revenue_cfg,
    )

    # --------------------------------------------------
    # Revenue exists
    # --------------------------------------------------
    assert "revenue" in result["mappings"]["col_map"]

    # --------------------------------------------------
    # Path updated from revenue_cfg
    # --------------------------------------------------
    assert result["mappings"]["col_map"]["revenue"]["path_revenue"] == "override.csv"

    # --------------------------------------------------
    # Label override must win
    # --------------------------------------------------
    assert result["mappings"]["col_map"]["revenue"]["rev_include_all_addresses"] is False
    from pprint import pprint
    pprint(result)

    # --------------------------------------------------
    # If revenue is None, flag should NOT create revenue block
    # --------------------------------------------------
    result_no_revenue = _build_v2_config(
        default_runner={
            "algorithm": {"APR": 0.03},
            "mappings": {"col_map": {}},
        },
        label_cfg={"rev_include_all_addresses": False, "overwrite": {}},
        apr_cfg=apr_cfg,
        revenue_cfg={"revenue label": "None", "revenue": None},
    )
    assert "revenue" not in result_no_revenue["mappings"]["col_map"]

if __name__ == "__main__":
    # test_build_v2_config_precedence()
    # test_build_v2_config_no_revenue()
    test_build_v2_config_rev_flag_behavior()
