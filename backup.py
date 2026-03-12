"""Database backup and restore functions."""

import os
import shutil
from datetime import datetime


def backup_database(db_path, backup_dir):
    """Copy the SQLite file to backup_dir with timestamp in filename.
    Returns the backup file path.
    """
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.splitext(os.path.basename(db_path))[0]
    backup_name = f"{base}_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)
    shutil.copy2(db_path, backup_path)
    return backup_path


def restore_database(backup_path, db_path):
    """Replace current DB file with selected backup."""
    shutil.copy2(backup_path, db_path)


def list_backups(backup_dir):
    """Return list of available backups with dates and sizes."""
    if not os.path.exists(backup_dir):
        return []
    backups = []
    for fname in sorted(os.listdir(backup_dir), reverse=True):
        if fname.endswith(".db"):
            fpath = os.path.join(backup_dir, fname)
            size = os.path.getsize(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
            backups.append({"filename": fname, "path": fpath, "size": size, "modified": mtime})
    return backups
