# Contributing

Velocity Tech University is a Django-based university portal. This repository continues an existing project codebase.

## Development setup

Follow the Windows setup in [README.md](README.md). Use a development Neon database and keep all credentials in `.env`.

## Change guidelines

- Preserve the existing Django project and app structure.
- Keep views role-protected and use Django forms, CSRF protection, and ORM validation.
- Add schema changes through Django migrations.
- Keep user-facing text in English and use the shared dashboard templates and styles.
- Do not add real student data, credentials, private API keys, or database dumps.
- Describe the changed files and include local setup or deployment notes with each change.

## License

The existing codebase is MIT-licensed. Keep the notice in [LICENSE](LICENSE) when distributing this project.
