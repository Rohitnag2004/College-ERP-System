# Velocity Tech University

Velocity Tech University is a Django-based portal for Admin, Teacher, and Student workflows. It uses Neon PostgreSQL for application records and Neon Object Storage (S3-compatible) for uploaded profile photos and learning resources.

## Features

- Role-aware sign-in and Student/Teacher registration
- Admin approval for Teacher accounts and management of users, academics, and assignments
- Course applications, attendance, results, fees, notices, and private learning resources
- Demo-only fee and teacher salary workflows; no money is transferred
- Independent Admin-controlled Student and Teacher maintenance switches
- Responsive dashboards, search, pagination, and five-minute idle session expiry

## Online storage

Production requires Neon PostgreSQL and a private Neon Object Storage bucket (or another private S3-compatible bucket). In production, uploaded files are not kept on the user's PC or the web host's local disk. Static assets are part of the deployed code and served by WhiteNoise. Storage and database credentials must be set in the hosting provider's secret environment, never committed to Git. Before moving existing uploads, run `migrate_media_to_object_storage` in dry-run mode, then review and apply the copy after configuring the bucket.

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for architecture, models, workflows, cloud storage setup, deployment, maintenance, and safe update instructions.

## Local development

Requires Python 3.10+ and the environment values in `.env.example`.

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a new `DJANGO_SECRET_KEY`, your Neon `DATABASE_URL`, and `DJANGO_DEBUG=true` in the ignored local `.env`. For cloud-only uploads, configure an S3-compatible private bucket and set `USE_REMOTE_MEDIA=true` plus its credentials. Local filesystem uploads should only be used for disposable development. Then run:

```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The source repository does not contain default account passwords or production secrets.

## Deployment

Configure the hosting provider's environment with `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, private object-storage credentials, and SMTP settings. Then run `python manage.py migrate` and `python manage.py collectstatic --noinput`; the `Procfile` starts Gunicorn.

## Licence

See [LICENSE](LICENSE) for the applicable licence.
