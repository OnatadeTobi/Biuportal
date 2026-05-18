"""Trim and normalize location strings from the client (no hostel whitelist)."""


def normalize_location(value: str) -> str:
    return ' '.join((value or '').strip().split())
