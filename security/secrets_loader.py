import os


def get_secret(key: str, default=None):
    """Return an environment value with a safe default.

    This centralizes how sensitive runtime configuration is read so future
    hardening can add external managers, masking, or audit hooks in one place.
    """
    return os.environ.get(key, default)
