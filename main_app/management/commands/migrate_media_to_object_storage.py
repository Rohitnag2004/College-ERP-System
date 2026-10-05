"""Copy legacy local uploads to the configured remote object storage."""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from main_app.models import CollegeResource, CustomUser


class Command(BaseCommand):
    help = "Dry-run by default; copy existing local profile images and college resources to remote storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Copy missing objects to the configured remote bucket and update stored file names.",
        )

    def handle(self, *args, **options):
        if not settings.USE_REMOTE_MEDIA:
            raise CommandError("Set USE_REMOTE_MEDIA=true and configure the bucket credentials first.")

        sources = []
        for user in CustomUser.objects.exclude(profile_pic="").iterator():
            name = user.profile_pic.name
            sources.append(("profile", user, user.profile_pic.storage, name, Path(settings.MEDIA_ROOT) / name))
        for resource in CollegeResource.objects.exclude(file="").iterator():
            name = resource.file.name
            sources.append(("resource", resource, resource.file.storage, name, settings.BASE_DIR / "private_resources" / name))

        copied = already_remote = missing = 0
        for kind, instance, storage, name, local_path in sources:
            if storage.exists(name):
                already_remote += 1
                continue
            if not local_path.is_file():
                missing += 1
                continue
            if not options["apply"]:
                copied += 1
                continue
            with local_path.open("rb") as source:
                remote_name = storage.save(name, File(source, name=Path(name).name))
            field = "profile_pic" if kind == "profile" else "file"
            setattr(instance, field, remote_name)
            instance.save(update_fields=(field,))
            copied += 1

        mode = "Copied" if options["apply"] else "Would copy"
        self.stdout.write(
            f"{mode}: {copied}; already in remote storage: {already_remote}; local source missing: {missing}."
        )
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Nothing was uploaded or changed. Review the counts, then use --apply."))
        if missing:
            self.stderr.write(self.style.WARNING("Some database file references have no local source. Check those records before cutover."))
