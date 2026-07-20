"""Canonical internal identifier helpers."""

from uuid import RFC_4122, UUID

from uuid6 import uuid7


def new_uuid7() -> UUID:
    """Generate a time-ordered RFC 9562 UUIDv7."""
    return uuid7()


def parse_uuid7(value: str) -> UUID:
    """Parse and validate the canonical representation of a UUIDv7."""
    parsed = UUID(value)
    if str(parsed) != value:
        raise ValueError("UUID must use the canonical lowercase hyphenated format")
    if parsed.version != 7 or parsed.variant != RFC_4122:
        raise ValueError("identifier must be an RFC 4122 variant UUIDv7")
    return parsed
