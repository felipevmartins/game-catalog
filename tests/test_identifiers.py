from uuid import uuid4

import pytest

from game_catalog.domain.identifiers import new_uuid7, parse_uuid7


def test_uuid7_is_canonical_and_ordered() -> None:
    first = new_uuid7()
    second = new_uuid7()

    assert first.version == 7
    assert parse_uuid7(str(first)) == first
    assert first < second


@pytest.mark.parametrize("value", [str(uuid4()), "019abcde-f000-7000-8000-00000000000a".upper()])
def test_uuid7_rejects_wrong_version_or_noncanonical_text(value: str) -> None:
    with pytest.raises(ValueError):
        parse_uuid7(value)
