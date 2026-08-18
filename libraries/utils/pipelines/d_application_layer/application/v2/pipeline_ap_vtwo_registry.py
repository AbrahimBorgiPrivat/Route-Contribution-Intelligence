from __future__ import annotations

from typing import Dict, List, Optional, Any

from libraries.utils.visualization.scenario_metadata_helpers import (
    _build_apr_explanations,
    _build_label_explanations,
    _build_revenue_explanations,
)
from libraries.utils.visualization.visualisation_helpers import (
    build_v2_registry_json,
    build_v2_scenario_metadata_json,
)

def build_v2_registry(
    *,
    save_dir: str,
    registry_filename: str = "registry.json",
    metadata_filename: str = "scenario_metadata.json",
    label_list: Optional[List[Dict[str, Any]]] = None,
    APR_profiles: Optional[List[Dict[str, Any]]] = None,
    revenue_list: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Build registry.json for Application v2 and shared scenario metadata.

    Parameters
    ----------
    save_dir : Root directory for v2 application data.
    registry_filename : Output filename (default: registry.json)
    metadata_filename : Output filename for shared scenario metadata

    Returns
    -------
    - Absolute path to written registry file.
    """
    label_explanations = _build_label_explanations(label_list)
    apr_explanations = _build_apr_explanations(APR_profiles)
    revenue_explanations = _build_revenue_explanations(revenue_list)

    build_v2_scenario_metadata_json(
        base_dir=save_dir,
        filename=metadata_filename,
        label_explanations=label_explanations,
        apr_explanations=apr_explanations,
        revenue_explanations=revenue_explanations,
    )

    return build_v2_registry_json(
        base_dir=save_dir,
        filename=registry_filename,
    )
