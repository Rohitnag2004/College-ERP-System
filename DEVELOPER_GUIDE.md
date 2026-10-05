# Velocity Tech University portal — developer guide

This guide is the hand-off reference for developers maintaining the portal. Read it before changing models, academic data, payment status, or file storage.

## What the application does

This is a Django 5.2 portal backed by PostgreSQL. It has separate role-aware flows for Admin, Teacher, and Student accounts.

- **Students** register, apply to one course, see the subjects for their assigned course/semester, review attendance and results, use the fee portal, read notices, download learning resources, and use the library/leave/feedback pages.
- **Teachers** register and wait for Admin approval. Once approved, a teacher sees their assigned course/semester/subjects, can take class attendance for the assigned class, submit their own work attendance, add results, publish learning resources for permitted audiences, and view salary records/receipts.
- **Admins** manage accounts, approvals, courses, subjects, sessions, assignments, attendance, results, fees/payments, notices/resources, teacher payroll, and whether the Student or Teacher portal is available during maintenance.

Demo payment and payroll screens do **not** transfer money. A fee receipt is available only after its fee-payment row is marked paid. A salary receipt is labelled demo-only and available after Payment Department approval.

## Main code map

| Path | Responsibility |
| --- | --- |
| `college_management_system/settings.py` | Environment variables, Neon database, timezone, security, static files, and remote upload storage. |
| `college_management_system/urls.py` | Root routes, Django auth routes, and local-only media serving. |
| `main_app/models.py` | Database schema and important uniqueness rules. |
| `main_app/forms.py` | Validation and form widgets for user, academic, resource, and fee data. |
| `main_app/views.py` | Login, role selection, signup, session activity, and legacy attendance lookup. |
| `main_app/hod_views.py` | Admin user/course/subject/session CRUD, class attendance review, results/leave/feedback and notifications. |
| `main_app/staff_views.py` | Teacher dashboard, assigned class attendance, results, own attendance, leave/feedback, and library operations. |
| `main_app/student_views.py` | Student dashboard, assigned-course attendance/results, profile, leave/feedback, notifications, and library. |
| `main_app/portal_views.py` | Course applications, fee schedules and demo payment review, fee receipts, learning resources, maintenance toggles, teacher payroll and salary receipts. |
| `main_app/middleware.py` | Role boundaries, teacher approval gate, Student/Teacher maintenance gate, and configurable idle session timeout (5 minutes by default). |
| `main_app/storage.py` | Private college-resource file storage; delegates to the private remote bucket in production. |
| `main_app/templates/` | Django HTML templates, divided into Admin, Teacher, Student, and shared layouts. |
| `main_app/static/` | Versioned application assets, including the university crest. These are application assets, not user uploads. |
| `main_app/migrations/` | Versioned schema migrations. Never edit an already-applied migration; create a new migration. |
| `main_app/data/brainware_catalog.json` | Academic catalogue extracted from the supplied workbook. It contains course, curriculum, lateral-entry, and fee-source data, not user passwords. |
| `main_app/management/commands/import_academic_catalog.py` | Dry-run-first academic catalogue replacement. `--replace` updates academic catalogue/history while preserving user identities; read the command before running it. |
| `main_app/management/commands/align_cohort_sessions.py` | Cohort/session alignment utility. Review its `--help` and use dry-run mode before applying changes. |
| `Procfile` | Gunicorn web process command for hosting. |

## Data model at a glance

- `CustomUser` is the shared email/password identity. `Admin`, `Staff`, and `Student` are role-specific profiles connected to it.
- `Course`, `Session`, `Semester`, and `Subject` hold academic structure. A subject belongs to a course and optionally a semester; teacher assignment is stored on the subject.
- `CourseRegistration` records a student's requested course/session and review status. A conditional database constraint prevents more than one approved course per student.
- `Attendance` is the class meeting; `AttendanceReport` is each student's status for that meeting. `TeacherAttendance` records a teacher's own check-in/out.
- `FeeStructure` is the course/session/semester charge and its active flag. `FeePayment` is the per-student status for that charge (`unpaid`, `pending`, `paid`, `rejected`). Do not mark it paid unless the payment was actually received or it is clearly identified as disposable demo data.
- `TeacherPayrollProfile` holds a demo bank/account destination. `SalaryPayment` stores each teacher/month salary record and Payment Department decision. No bank transfer is integrated.
- `Notice` contains text announcements. `CollegeResource` contains uploaded notes/modules/academic files and an audience (`students` or `teachers`). Resource downloads pass through an authenticated audience check.
- `PortalAccessSettings` stores separate Student and Teacher maintenance switches; Admin access remains available.

## Access and workflow rules

1. Role login selection is presented on the shared login page. The server still checks the account role; hiding a menu item is not an access-control boundary.
2. Student sign-up can create a Student account and submit a course application. The application flow currently approves eligible student course registration as implemented in `student_course_registration`; review before changing that policy.
3. Teacher sign-up does not grant portal access until Admin approves the account. Subject assignment is administered by Admin and affects the Teacher's available attendance/resource actions.
4. Students see only their own course/semester data and payments. Teachers see only their assigned subjects/classes and their own salary history. Admin-only views are protected by role decorators and/or `LoginCheckMiddleWare`.
5. Attendance pages should select subjects through the course/session filter; keep the subject label short (code/name) while retaining the semester ID for server-side filtering.
6. The five-minute idle timeout is enforced in middleware and the client interaction script. `SESSION_IDLE_TIMEOUT_SECONDS` can override the default; keep both checks in sync and verify background-tab resume, AJAX requests, and active upload/download flows.
7. Maintenance is reversible: the Admin can independently disable and re-enable Student and Teacher portals under **Portal Availability**.
8. Demo fee approval/cash recording and demo salary approval create local portal records only. They are not payment processor integrations.

## Online data and file storage

The production deployment is designed not to rely on the user's PC or the web process's local disk for persistent data:

- **Database records:** Neon PostgreSQL via `DATABASE_URL`. Neon transaction pooling is configured with Django server-side cursors disabled to avoid invalid-cursor errors.
- **Uploaded profile photos and learning-resource files:** private Neon Object Storage (S3-compatible). The default production setting is `USE_REMOTE_MEDIA=true`; startup fails with a clear configuration error if the bucket credentials are missing. `django-storages` uses signed URLs for private objects. Keep the bucket private.
- **Static code assets and crest:** committed under `main_app/static/`; `collectstatic` gathers them for WhiteNoise at deployment. They are version-controlled application assets, not uploaded user data.
- **Email:** production SMTP is configured through environment variables. Local debug defaults to console email.
- **Secrets:** `.env` is only for a developer's local environment and is git-ignored. Production secrets belong in the hosting provider's environment/secret settings. Never commit or share `DATABASE_URL`, Django secret, storage keys, or SMTP password.

### Configure the remote bucket

Create a private bucket on the same Neon branch as the production database in Neon Console or Neon infrastructure config. Neon Object Storage speaks the S3 protocol and uses branch-scoped AWS-compatible credentials. Neon does not use S3 ACL or bucket-policy mutation calls to control bucket visibility; set the bucket to private in Neon. Alternatively, use a private AWS S3 or other S3-compatible bucket. Set these values in the hosting provider, not in source code:

| Environment variable | Value |
| --- | --- |
| `USE_REMOTE_MEDIA` | `true` |
| `AWS_STORAGE_BUCKET_NAME` | Exact bucket name |
| `AWS_ACCESS_KEY_ID` | Bucket-scoped access key |
| `AWS_SECRET_ACCESS_KEY` | Matching secret key |
| `AWS_ENDPOINT_URL_S3` | Neon branch S3 endpoint; leave blank for AWS S3 |
| `AWS_REGION` | Region supplied for the Neon branch endpoint; AWS bucket region for S3 |
| `AWS_S3_ADDRESSING_STYLE` | `path` for Neon Object Storage; `auto` can be used for AWS |

For Neon, use the bucket name and `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL_S3`, and `AWS_REGION` values supplied for the production branch. The app also accepts `AWS_S3_ENDPOINT_URL` and `AWS_S3_REGION_NAME` as compatibility names for existing providers. The same private bucket is split into `media/` for profile images and `private_resources/` for access-checked course files.

For a local developer who also wants uploads to go to the online bucket, set the same remote-storage variables and `USE_REMOTE_MEDIA=true` in the ignored local `.env`. With remote storage enabled, profile images are stored under `media/` and access-controlled college files under `private_resources/` in that bucket. The Django app never serves private resources from `MEDIA_ROOT` in production.

Local `DEBUG=true` can use filesystem storage only as a development fallback. Do not treat files created by that fallback as production data. Production defaults to remote storage and refuses to run with local upload storage.

### Existing local uploads

Switching to remote storage does not automatically copy files that were previously saved under local `media/` or `private_resources/`. A dry-run-first command is available once the bucket is configured:

```powershell
python manage.py migrate_media_to_object_storage
python manage.py migrate_media_to_object_storage --apply
```

The first command only reports counts. The second copies profile images and learning-resource files and updates database file names; it deliberately keeps local originals. Verify the reported remote objects and open files through the portal before archiving local copies. This checkout currently has a small local `media/` folder and no local `private_resources/` files; no remote copy has been run because the bucket credentials have not been configured.

## Setup and deploy

### Local development

1. Install Python 3.10+ and dependencies: `python -m pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`. Add a new `DJANGO_SECRET_KEY` and the Neon `DATABASE_URL`. Set `DJANGO_DEBUG=true`, local allowed hosts, and `USE_REMOTE_MEDIA=false` only if using local development uploads; configure the remote bucket instead if no local uploads should be written.
3. Run `python manage.py migrate` and `python manage.py runserver`.
4. On Windows, run `.\run_local.ps1` to start the local preview. It connects to the configured Neon database and uses a per-process DNS fallback if the router cannot resolve Neon; it does not change Windows network settings or copy database records locally. Open `http://127.0.0.1:8000/`. Use the existing Admin account; the source repository intentionally contains no default passwords.

### Production

1. Connect the repository to a Django-capable host and set the `Procfile` command. The app itself must run on a web host; Neon provides the database and object storage, not Django hosting.
2. Configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, and all remote-bucket variables in the host's secret settings.
3. Configure SMTP (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`).
4. Build/install requirements, run `python manage.py migrate`, then `python manage.py collectstatic --noinput`, then start Gunicorn.
5. Verify sign-in by each role, role boundaries, student/teacher maintenance switches, a private resource download, a sample fee flow, and a demo salary receipt before inviting users.

### GitHub upload checklist

- This project folder may come from a ZIP and may not contain a `.git` directory. Initialize Git only when ready to create its repository, then review `git status` before committing.
- `.env`, SQLite databases, local uploads, generated `tmp/` files and scripts, and the unrelated `reports_and _resource/` folder are ignored. Do not force-add them.
- Keep the academic catalogue, migrations, templates, static application assets, requirements, and documentation. Never upload `.env` or actual storage/database/SMTP credentials.
- `main_app/static/image/admin-signature.jpg` is the receipt signature asset. Treat it as sensitive; use a private GitHub repository if you keep this asset in source. A public repository makes the source asset publicly downloadable.
- GitHub stores source code; it does not host this Django app or provide durable user uploads. Production needs a Django-capable host, Neon PostgreSQL, and a private object-storage bucket configured before enabling uploads.

The test module has public-portal smoke tests for the shared login page, its role choices and CAPTCHA prompt, legacy role URL redirects, and invalid-role handling. Run tests with an in-memory SQLite database; do not point a test run at the live Neon database. These checks do not replace role-by-role smoke checks on a disposable environment before production deployment.

## Safe change workflow

- Inspect the relevant model, view, URL, and template together before editing a feature.
- For a schema edit, create a new migration with `python manage.py makemigrations`, inspect it, then apply with `python manage.py migrate`.
- Use `python manage.py check` and review URL/template behavior after a change. Do not run catalogue `--replace` against live data without reviewing its dry-run and taking a backup.
- Avoid large unpaginated querysets. Use `select_related`/`prefetch_related` when rendering related rows and preserve search/pagination on long tables.
- Keep permissions enforced server-side. Uploaded learning resources must continue through `download_learning_resource` and its role/audience checks.
- Never put credentials in templates, source, fixtures, screenshots, Git commits, or user-facing logs.

## Known operational notes

- Production uses `Asia/Kolkata` and timezone-aware timestamps.
- The example `.env` is not a credential source. Use fresh user-owned secrets in a host environment.
- The fee and salary flows are simulation features. Integrating a real payment or bank provider would require a separate approved design and reconciliation workflow.
- Keep `main_app/data/brainware_catalog.json` aligned with the approved academic source workbook; importing it can replace academic history even though accounts are preserved.
