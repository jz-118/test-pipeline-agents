import pytest

from pipeline_agent.demo_target import normalize_username


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" Alice ", "alice"),
        ("BOB", "bob"),
        ("  Demo-User  ", "demo-user"),
    ],
)
def test_normalize_username(raw, expected):
    assert normalize_username(raw) == expected


def test_normalize_username_rejects_empty_value():
    with pytest.raises(ValueError, match="must not be empty"):
        normalize_username("   ")
