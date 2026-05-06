import os

def get_secret(key: str, default=None):
    """Return a secret-like environment value with a safe default.

    This centralizes how environment secrets are read to enable future
    enhancements (e.g., secret managers, masking in logs, etc.).
    """
    return os.environ.get(key, default)
