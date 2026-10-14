"""
sample_safe_telematics.py
Secure automotive telematics handler demonstrating recommended coding guidelines.
Expected static analysis findings: 0
"""

import os
import hashlib
import subprocess
import logging
from typing import Optional, List

logger = logging.getLogger("TelematicsService")


def get_auth_token() -> str:
    """Retrieves secret from environment instead of hardcoded string."""
    token = os.environ.get("ECU_AUTH_TOKEN")
    if not token:
        raise ValueError("Missing ECU_AUTH_TOKEN configuration.")
    return token


def verify_firmware_sha256(firmware_bytes: bytes) -> str:
    """Uses NIST-approved SHA-256 for cryptographic digest verification."""
    hasher = hashlib.sha256()
    hasher.update(firmware_bytes)
    return hasher.hexdigest()


def execute_diagnostic_binary(args: List[str], timeout_sec: int = 5) -> str:
    """Runs binary using argument array with shell=False and strict timeout."""
    if not args or not all(isinstance(a, str) for a in args):
        raise ValueError("Invalid argument list provided.")
    try:
        proc = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=True
        )
        return proc.stdout
    except subprocess.TimeoutExpired:
        logger.error("Diagnostic execution timed out.")
        raise
    except subprocess.CalledProcessError as exc:
        logger.error("Diagnostic failed with return code %d", exc.returncode)
        raise


def record_sensor_metric(metric_val: float, store: Optional[List[float]] = None) -> List[float]:
    """Uses None default for mutable argument to avoid shared state."""
    active_store = store if store is not None else []
    active_store.append(metric_val)
    return active_store
