from __future__ import annotations

from typing import Any, Dict, List, Optional


def _get_first_string(
    entry: Dict[str, Any],
    candidate_keys: List[str],
) -> Optional[str]:
    for key in candidate_keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_label_explanations(
    label_list: Optional[List[Dict[str, Any]]],
) -> Dict[str, str]:
    explanations: Dict[str, str] = {}
    if not label_list:
        return explanations
    for label_cfg in label_list:
        label = label_cfg.get("c_cache_config", {}).get("label")
        if not label:
            continue
        explanation = _get_first_string(
            label_cfg,
            ["label_explanation", "explanation", "description"],
        )
        if explanation:
            explanations[label] = explanation
    return explanations


def _build_apr_explanations(
    APR_profiles: Optional[List[Dict[str, Any]]],
) -> Dict[str, str]:
    explanations: Dict[str, str] = {}
    if not APR_profiles:
        return explanations
    for apr_cfg in APR_profiles:
        label = apr_cfg.get("APR Label")
        if not label:
            continue
        explanation = _get_first_string(
            apr_cfg,
            [
                "APR_profile_explanation",
                "APR_explanation",
                "explanation",
                "description",
            ],
        )
        if explanation:
            explanations[label] = explanation
    return explanations


def _build_revenue_explanations(
    revenue_list: Optional[List[Dict[str, Any]]],
) -> Dict[str, str]:
    explanations: Dict[str, str] = {}
    if not revenue_list:
        return explanations
    for revenue_cfg in revenue_list:
        label = revenue_cfg.get("revenue label")
        if not label:
            continue
        explanation = _get_first_string(
            revenue_cfg,
            [
                "revenue_explanation",
                "week_profile_explanation",
                "Week_Profile_explanation",
                "explanation",
                "description",
            ],
        )
        if explanation:
            explanations[label] = explanation
    return explanations
