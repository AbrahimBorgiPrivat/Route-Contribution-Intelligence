from libraries.utils.visualization.scenario_metadata_helpers import (
    _get_first_string,
)


def test__get_first_string_returns_first_non_empty_trimmed_string():
    entry = {
        "description": "   ",
        "explanation": "  valgt forklaring  ",
        "label_explanation": "skal ikke bruges",
    }

    result = _get_first_string(
        entry,
        ["description", "explanation", "label_explanation"],
    )

    assert result == "valgt forklaring"


def test__get_first_string_returns_none_when_no_valid_string_exists():
    entry = {
        "description": None,
        "explanation": "   ",
        "label_explanation": 123,
    }

    result = _get_first_string(
        entry,
        ["description", "explanation", "label_explanation"],
    )

    assert result is None
