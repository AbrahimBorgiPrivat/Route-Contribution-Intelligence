from libraries.utils.visualization.scenario_metadata_helpers import (
    _build_revenue_explanations,
)


def test__build_revenue_explanations_prefers_revenue_explanation():
    revenue_list = [
        {
            "revenue label": "U36",
            "revenue_explanation": "  Uge 36 forklaring  ",
            "week_profile_explanation": "Fallback",
        }
    ]

    result = _build_revenue_explanations(revenue_list)

    assert result == {"U36": "Uge 36 forklaring"}


def test__build_revenue_explanations_uses_week_profile_fallback():
    revenue_list = [
        {
            "revenue label": "Gns. Oms",
            "week_profile_explanation": "Gennemsnitlig forklaring",
        }
    ]

    result = _build_revenue_explanations(revenue_list)

    assert result == {"Gns. Oms": "Gennemsnitlig forklaring"}


def test__build_revenue_explanations_skips_invalid_entries():
    revenue_list = [
        {
            "revenue label": "U36",
            "revenue_explanation": "Forklaring",
        },
        {
            "revenue label": "U37",
            "revenue_explanation": "   ",
        },
        {
            "revenue_explanation": "Ingen label",
        },
    ]

    result = _build_revenue_explanations(revenue_list)

    assert result == {"U36": "Forklaring"}
