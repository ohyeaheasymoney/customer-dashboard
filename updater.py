"""One-click version updater — pulls latest code from GitHub."""

import os
import subprocess

APP_DIR = os.path.dirname(__file__)
VERSION_FILE = os.path.join(APP_DIR, "version.json")

# Bump this when releasing
CURRENT_VERSION = "2.1.0"


def get_version():
    """Return the current app version string."""
    return CURRENT_VERSION


def check_for_updates():
    """Check GitHub for newer commits. Returns (has_update, message)."""
    try:
        result = subprocess.run(
            ["git", "fetch", "--dry-run"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=15
        )
        # After fetch, check if we're behind
        result = subprocess.run(
            ["git", "fetch"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=15
        )
        status = subprocess.run(
            ["git", "status", "-uno"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10
        )
        output = status.stdout
        if "Your branch is behind" in output:
            # Extract how many commits behind
            for line in output.splitlines():
                if "behind" in line:
                    return True, line.strip()
            return True, "Updates available"
        elif "Your branch is up to date" in output:
            return False, "You're on the latest version"
        else:
            return False, "Could not determine update status"
    except FileNotFoundError:
        return False, "Git is not installed"
    except subprocess.TimeoutExpired:
        return False, "Network timeout — check your connection"
    except Exception as e:
        return False, f"Error checking for updates: {e}"


def apply_update():
    """Pull latest code from GitHub. Returns (success, message)."""
    try:
        # Stash any local changes first
        subprocess.run(
            ["git", "stash"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10
        )
        # Pull latest
        result = subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, "Update successful!\nRestart the app to use the new version."
        else:
            # Try without rebase
            result = subprocess.run(
                ["git", "pull"],
                cwd=APP_DIR, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return True, "Update successful!\nRestart the app to use the new version."
            return False, f"Update failed:\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "Network timeout — check your connection"
    except Exception as e:
        return False, f"Update error: {e}"
