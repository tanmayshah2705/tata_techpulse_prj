"""
sample_vulnerable_ecu.py
Demonstration automotive ECU diagnostic service containing security defects.
For testing AutoCodeGuard review capabilities.
"""

import os
import hashlib
import subprocess

# Vulnerability 1: Hardcoded credentials
DIAGNOSTIC_API_KEY = "SECRET_ECU_ACCESS_TOKEN_2027"
ADMIN_PASSWORD = "ecu_super_admin_pass"

# Vulnerability 2: Insecure debug mode flag enabled in production
DEBUG = True


def handle_remote_command(user_command: str):
    """Executes a diagnostic routine from remote telematics."""
    # Vulnerability 3: Dangerous dynamic evaluation
    print(f"[DEBUG] Executing command: {user_command}")
    return eval(user_command)


def trigger_firmware_update(image_path: str):
    """Spawns an update process via OS shell."""
    # Vulnerability 4: Insecure subprocess with shell=True
    cmd = f"/opt/ecu/bin/flash_tool --file {image_path}"
    subprocess.run(cmd, shell=True)


def verify_image_checksum(firmware_bytes: bytes):
    """Verifies firmware integrity using legacy hashing."""
    # Vulnerability 5: Broken cryptographic algorithm (MD5)
    hasher = hashlib.md5()
    hasher.update(firmware_bytes)
    return hasher.hexdigest()


def read_sensor_metrics(sensor_id: int, cache_list=[]):
    """Collects telemetry from CAN bus sensor."""
    # Vulnerability 6: Mutable default argument
    try:
        cache_list.append(sensor_id)
        # TODO: Implement secure CAN ID validation
        return cache_list
    except:
        # Vulnerability 7: Bare except hiding critical faults
        pass
