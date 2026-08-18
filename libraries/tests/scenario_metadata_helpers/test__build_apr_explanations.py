from libraries.utils.visualization.scenario_metadata_helpers import (
    _build_apr_explanations,
)


def test__build_apr_explanations_prefers_apr_profile_explanation():
    apr_profiles = [
        {
            "APR Label": "SE Omdeler",
            "APR_profile_explanation": "  Profil forklaring  ",
            "APR_explanation": "Fallback",
        }
    ]

    result = _build_apr_explanations(apr_profiles)

    assert result == {"SE Omdeler": "Profil forklaring"}


def test__build_apr_explanations_uses_fallback_keys():
    apr_profiles = [
        {
            "APR Label": "O18 Omdeler",
            "description": "Beskrivelse",
        }
    ]

    result = _build_apr_explanations(apr_profiles)

    assert result == {"O18 Omdeler": "Beskrivelse"}


def test__build_apr_explanations_returns_empty_dict_for_none():
    assert _build_apr_explanations(None) == {}
