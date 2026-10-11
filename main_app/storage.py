"""Private storage for files that must only be served after role checks."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateResourceStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        self._remote_storage = None
        if settings.USE_REMOTE_MEDIA:
            from storages.backends.s3 import S3Storage

            remote_location = location or "private_resources"
            self._remote_storage = S3Storage(
                location=remote_location,
                default_acl=None,
                querystring_auth=True,
                file_overwrite=False,
            )
            super().__init__(location=remote_location, base_url=base_url or "")
            return
        super().__init__(
            location=location or settings.PRIVATE_RESOURCES_ROOT,
            # Deliberately not MEDIA_URL: these files are only served by the
            # authenticated, role-checked download view.
            base_url=base_url or "/_private-resources-not-served/",
        )

    def _open(self, name, mode="rb"):
        return self._remote_storage._open(name, mode) if self._remote_storage else super()._open(name, mode)

    def _save(self, name, content):
        return self._remote_storage._save(name, content) if self._remote_storage else super()._save(name, content)

    def delete(self, name):
        return self._remote_storage.delete(name) if self._remote_storage else super().delete(name)

    def exists(self, name):
        return self._remote_storage.exists(name) if self._remote_storage else super().exists(name)

    def listdir(self, path):
        return self._remote_storage.listdir(path) if self._remote_storage else super().listdir(path)

    def size(self, name):
        return self._remote_storage.size(name) if self._remote_storage else super().size(name)

    def url(self, name):
        return self._remote_storage.url(name) if self._remote_storage else super().url(name)

    def path(self, name):
        return self._remote_storage.path(name) if self._remote_storage else super().path(name)

    def get_accessed_time(self, name):
        return self._remote_storage.get_accessed_time(name) if self._remote_storage else super().get_accessed_time(name)

    def get_created_time(self, name):
        return self._remote_storage.get_created_time(name) if self._remote_storage else super().get_created_time(name)

    def get_modified_time(self, name):
        return self._remote_storage.get_modified_time(name) if self._remote_storage else super().get_modified_time(name)
