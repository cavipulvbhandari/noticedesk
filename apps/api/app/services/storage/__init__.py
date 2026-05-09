"""Vendor-abstracted blob storage.

Production uses :class:`S3Storage` (AWS Mumbai). Dev/CI uses
:class:`LocalStorage` writing to a configured directory. Both share the same
async interface so call sites never change.
"""

from app.services.storage.base import ObjectMetadata, Storage, StorageError
from app.services.storage.factory import get_storage

__all__ = ["ObjectMetadata", "Storage", "StorageError", "get_storage"]
