"""
Storage utilities for Event Planner project.
"""

import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage


def generate_unique_filename(filename):
    """
    Generate a unique filename preserving the extension.
    """
    ext = os.path.splitext(filename)[1]
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{ext}"


def upload_file(file, folder='uploads'):
    """
    Upload file to storage backend.
    """
    filename = generate_unique_filename(file.name)
    path = f"{folder}/{filename}"
    saved_path = default_storage.save(path, file)
    return saved_path


def get_file_url(path):
    """
    Get URL for a stored file.
    """
    if not path:
        return None
    return default_storage.url(path)


def delete_file(path):
    """
    Delete a file from storage.
    """
    if path and default_storage.exists(path):
        default_storage.delete(path)
        return True
    return False
