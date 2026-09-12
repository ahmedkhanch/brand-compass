"""Security-specific helpers; shared HTTP fixtures live in tests.conftest."""


def bearer(subject):
    return {"Authorization": f"Bearer {subject}"}
