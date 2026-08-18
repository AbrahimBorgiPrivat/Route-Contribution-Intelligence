from libraries.utils.visualization.scenario_metadata_helpers import (
    _build_label_explanations,
)


def test__build_label_explanations_prefers_label_explanation():
    label_list = [
        {
            "c_cache_config": {"label": "Label A"},
            "label_explanation": "  Forklaring A  ",
            "description": "Fallback",
        }
    ]

    result = _build_label_explanations(label_list)

    assert result == {"Label A": "Forklaring A"}


def test__build_label_explanations_skips_missing_label_or_explanation():
    label_list = [
        {
            "c_cache_config": {"label": "Label A"},
            "label_explanation": "Forklaring A",
        },
        {
            "c_cache_config": {"label": "Label B"},
        },
        {
            "label_explanation": "Ingen label",
        },
    ]

    result = _build_label_explanations(label_list)

    assert result == {"Label A": "Forklaring A"}


def test__build_label_explanations_returns_empty_dict_for_none():
    assert _build_label_explanations(None) == {}
