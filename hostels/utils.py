"""Hostel string normalization for storage and comparison."""

# Canonical names used by seed command / QR setup (not exposed via API).
MVP_HOSTEL_NAMES = [
    'Hope Hostel',
    'Above Only Hostel',
    'Peace Hostel',
    'Balm of Gilead',
    'Grace Hostel',
]

_CANONICAL_BY_KEY = {name.casefold(): name for name in MVP_HOSTEL_NAMES}


def normalize_hostel_for_storage(hostel: str) -> str:
    """Trim and collapse internal whitespace."""
    return ' '.join(hostel.strip().split())


def canonicalize_hostel(hostel: str) -> str:
    """Map known hostel names to canonical spelling; otherwise return trimmed input."""
    stored = normalize_hostel_for_storage(hostel)
    return _CANONICAL_BY_KEY.get(stored.casefold(), stored)


def hostels_match(hostel_a: str, hostel_b: str) -> bool:
    """Case-insensitive, whitespace-normalized hostel comparison."""
    return (
        normalize_hostel_for_storage(hostel_a).casefold()
        == normalize_hostel_for_storage(hostel_b).casefold()
    )
