import copy

def _deep_update(base: dict, override: dict) -> dict:
    """
    Recursively updates dict 'base' with 'override'.

    Special rule:
    - 'problem_type' is always replaced, never deep-merged.
    """
    for key, value in override.items():
        if key == "problem_type":
            base[key] = value
            continue
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base

def _build_v2_config(
    default_runner: dict,
    label_cfg: dict,
    apr_cfg: dict,
    revenue_cfg: dict,
) -> dict:
    """
    Build final flat config using precedence:

    label_cfg > apr_cfg > revenue_cfg > default_runner
    """
    config = copy.deepcopy(default_runner)
    # -------------------------------------------------
    # Apply revenue overrides
    # -------------------------------------------------
    if revenue_cfg.get("revenue") is not None:
        if "mappings" not in config:
            config["mappings"] = {}
        if "col_map" not in config["mappings"]:
            config["mappings"]["col_map"] = {}

        config["mappings"]["col_map"]["revenue"] = revenue_cfg["revenue"]
    # -------------------------------------------------
    # Apply APR overrides
    # -------------------------------------------------
    config["algorithm"]["APR"] = apr_cfg["APR"]
    # -------------------------------------------------
    # Apply label overrides (highest priority)
    # -------------------------------------------------
    overwrite = label_cfg.get("overwrite", {})
    _deep_update(config, overwrite)
    # -------------------------------------------------
    # Add label-level revenue flag if declared
    # -------------------------------------------------
    rev_flag = label_cfg.get("rev_include_all_addresses")
    if rev_flag is not None:
        if "mappings" in config and "col_map" in config["mappings"]:
            if "revenue" in config["mappings"]["col_map"]:
                config["mappings"]["col_map"]["revenue"][
                    "rev_include_all_addresses"
                ] = rev_flag

    return config