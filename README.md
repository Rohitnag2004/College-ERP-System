<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=38&pause=800&color=67E8F9&background=0B1020&center=true&vCenter=true&width=950&height=100&lines=VELOCITY+TECH+UNIVERSITY;ACADEMIC+ERP+PLATFORM;ONE+CAMPUS+%E2%80%A2+THREE+WORKSPACES;ADMIN+%E2%80%A2+TEACHER+%E2%80%A2+STUDENT" alt="Animated Velocity Tech University title" />

### COLLEGE ERP &nbsp;·&nbsp; ACADEMIC MANAGEMENT &nbsp;·&nbsp; CAMPUS WORKFLOWS

A connected campus platform for students, teachers, and administrators.

[![LIVE SERVICE](https://img.shields.io/website?url=https%3A%2F%2Fvelocity-tech-university.onrender.com&style=for-the-badge&label=SERVICE&up_message=ONLINE&down_message=CHECKING)](https://velocity-tech-university.onrender.com)

[![OPEN LIVE WEBSITE](https://img.shields.io/badge/OPEN%20LIVE%20WEBSITE-velocity--tech--university.onrender.com-22d3ee?style=for-the-badge&logo=render&logoColor=white)](https://velocity-tech-university.onrender.com)

[![Django CI](https://github.com/Rohitnag2004/College-ERP-System/actions/workflows/django.yml/badge.svg)](https://github.com/Rohitnag2004/College-ERP-System/actions/workflows/django.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)
![Hosted on Render](https://img.shields.io/badge/Hosted%20on-Render-46E3B7?logo=render&logoColor=0B1020)

[Live portal](https://velocity-tech-university.onrender.com) &nbsp; ✦ &nbsp; [Source code](https://github.com/Rohitnag2004/College-ERP-System) &nbsp; ✦ &nbsp; [Developer guide](DEVELOPER_GUIDE.md)

<img src="https://readme-typing-svg.demolab.com?font=Space+Mono&size=16&pause=1200&color=A78BFA&center=true&vCenter=true&width=850&height=38&lines=ONE+CONNECTED+CAMPUS;ACADEMIC+WORKFLOWS+IN+ONE+PLACE;BUILT+FOR+ADMIN+%E2%80%A2+TEACHER+%E2%80%A2+STUDENT" alt="Animated campus platform highlights" />

</div>

---

## ◈ NAVIGATION

[Overview](#-the-platform) &nbsp;·&nbsp; [Dashboards](#-role-dashboards) &nbsp;·&nbsp; [Gallery](#-dashboard-gallery) &nbsp;·&nbsp; [Features](#-core-modules) &nbsp;·&nbsp; [Run locally](#-run-it-on-your-laptop) &nbsp;·&nbsp; [Roadmap](#roadmap)

## ✦ THE PLATFORM

**Velocity Tech University ERP** brings academic and administrative work together in one Django application. Role-based access gives administrators, teachers, and students their own protected dashboards and workflows.

| LIVE DEMO | CLOUD PLATFORM |
|---|---|
| [velocity-tech-university.onrender.com](https://velocity-tech-university.onrender.com) | Django · Neon PostgreSQL · S3-compatible media storage |

> Render Free may spin the service down while idle. The first visit after a quiet period can take around a minute to wake up.

**Project goal:** give every campus role a clear, focused workspace while keeping shared academic information in one system.

## ◈ ROLE DASHBOARDS

Choose a dashboard to open. Each page requires an account with the matching role and a successful sign-in.

| ADMINISTRATOR | TEACHER | STUDENT |
|---|---|---|
| [Open Admin Dashboard ↗](https://velocity-tech-university.onrender.com/admin/home/) | [Open Teacher Dashboard ↗](https://velocity-tech-university.onrender.com/staff/home/) | [Open Student Dashboard ↗](https://velocity-tech-university.onrender.com/student/home/) |
| Manages users, courses, approvals, and academic operations. | Manages attendance, results, resources, and classroom tasks. | Views attendance, results, courses, fees, and study resources. |

[Sign in](https://velocity-tech-university.onrender.com/) &nbsp;·&nbsp; [Student registration](https://velocity-tech-university.onrender.com/register/student/) &nbsp;·&nbsp; [Teacher registration](https://velocity-tech-university.onrender.com/register/teacher/)

Teacher accounts require administrator approval. Administrator accounts are created by an existing administrator. Dashboard links do not provide access to another user's account.

### Typical role journeys

- **Administrator:** maintain courses, subjects, sessions, accounts, and approvals; review academic activity and institutional records.
- **Teacher:** open assigned classes, record attendance and results, share learning material, and follow leave or feedback requests.
- **Student:** check attendance and results, request course registration, open learning resources, and follow notices and fee records.

## ◈ DASHBOARD GALLERY

### 01 · ADMINISTRATOR CONTROL CENTER

<img src="docs/screenshots/admin-dashboard.png" alt="Administrator dashboard preview" width="100%" />

*Monitor students, teachers, courses, subjects, and academic activity from the admin dashboard.*

### 02 · STUDENT LEARNING SPACE

<img src="docs/screenshots/student-dashboard.png" alt="Student dashboard preview" width="100%" />

*Check attendance, results, course registration, notices, fees, and learning resources.*

### 03 · TEACHER WORKSPACE

<img src="docs/screenshots/teacher-dashboard.png" alt="Teacher dashboard preview" width="100%" />

*Manage classroom attendance, results, leave requests, library books, and student resources.*

<sub>Dashboard screenshots may contain account names and sample information.</sub>

The gallery shows the three role-specific interfaces side by side in purpose: administration, teaching, and student learning. The dashboard links above open the corresponding protected pages on the live app.

## ✦ CORE MODULES

<table>
<tr>
<td width="50%" valign="top">
<h3>◉ Academic operations</h3>
Courses · subjects · sessions · attendance · results · grade cards · course registration
</td>
<td width="50%" valign="top">
<h3>◉ Campus administration</h3>
Student and teacher records · approvals · assignments · portal availability · fee records
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>◉ Learning & communication</h3>
Notices · notifications · library · learning resources · leave requests · feedback
</td>
<td width="50%" valign="top">
<h3>◉ Cloud-ready foundation</h3>
Neon PostgreSQL · private S3-compatible uploads · WhiteNoise static files · Gunicorn
</td>
</tr>
</table>

> Fee and salary screens are demonstration workflows. They do not process payments or transfer money.

### Module guide

| Area | Examples |
|---|---|
| Academic records | Courses, subjects, sessions, attendance, results, grade cards |
| People and access | Student and teacher records, teacher approvals, role-specific pages |
| Classroom workflows | Attendance taking, result entry, course assignments, leave requests |
| Student services | Course registration, notices, fees, library books, study resources |
| Administration | Portal availability, course-registration review, fee-payment review, reports |
| Communication | Notifications, feedback, notices, learning-resource sharing |

## ◈ SYSTEM MAP

A user signs in to a role-based Django portal. The application reads academic records from PostgreSQL and saves configured uploads to private S3-compatible object storage. Static assets are collected during deployment and served by WhiteNoise.

```mermaid
flowchart LR
    Browser[Web browser] --> ERP[Django ERP]
    ERP --> Roles[Role-based access]
    ERP --> Academic[Academic workflows]
    ERP --> Admin[Administrative workflows]
    Roles --> DB[(Neon PostgreSQL)]
    Academic --> DB
    Admin --> DB
    ERP --> Media[(S3-compatible object storage)]
    ERP --> Static[WhiteNoise static assets]
```

## ✦ TECHNOLOGY STACK

| Layer | Technology |
|---|---|
| Web application | Python 3.12+ · Django 5.2 |
| Database | PostgreSQL · Neon |
| Uploaded media | Neon Object Storage · S3-compatible API |
| Production server | Gunicorn · WhiteNoise |
| Hosting | Render |
| Continuous integration | GitHub Actions |

## 🚀 RUN IT ON YOUR LAPTOP

This walkthrough is for a local development copy. It will not connect to the deployed website unless you deliberately configure your own database URL. Keep local and production credentials separate.

New to Django? Follow these Windows steps to download the project and start a local copy. You need **Python 3.12+**, **Git**, and access to a **PostgreSQL database**. Use your own database; do not use someone else's production credentials. Local uploads can be saved on your laptop, so no object-storage account is needed for this local setup.

### 1 · Install Python and Git

- Install [Python 3.12+](https://www.python.org/downloads/). During setup, select **Add Python to PATH**.
- Install [Git for Windows](https://git-scm.com/downloads).
- Make sure you have a PostgreSQL connection URL for a database you own or are allowed to use.

### 2 · Download the source

Open **PowerShell** and enter:

```powershell
git clone https://github.com/Rohitnag2004/College-ERP-System.git
cd College-ERP-System
```

### 3 · Create your isolated Python environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, continue with `.\.venv\Scripts\python.exe` instead of `python` in the commands below. This avoids changing your computer's script security settings.

### 4 · Install the requirements

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5 · Add your private local settings

```powershell
Copy-Item .env.example .env
notepad .env
```

In `.env`, enter your own values. For local development, the main settings look like:

```dotenv
DJANGO_SECRET_KEY=replace-this-with-a-long-random-local-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_HOST/YOUR_DATABASE
USE_REMOTE_MEDIA=false
```

Replace the database URL with your own PostgreSQL connection string. Save `.env` on your laptop; **never upload it to GitHub or share it in screenshots**. `DJANGO_DEBUG=true` is for local use only.

### 6 · Prepare the database and launch

```powershell
python manage.py migrate
python manage.py runserver
```

Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**. Register a student or teacher account through the site. A teacher must be approved by an administrator before signing in. The project does not include public demo passwords.

**If setup fails:** confirm Python and Git are installed, `.env` exists in the project folder, and `DATABASE_URL` points to a reachable PostgreSQL database. Never paste passwords or secret values into an issue.

### Quick troubleshooting

| Message or symptom | What to check |
|---|---|
| `py` or `python` is not recognized | Reinstall Python and select **Add Python to PATH**, then open a new PowerShell window. |
| `DATABASE_URL` is missing or invalid | Check the `.env` filename, database URL, and database network access. |
| `No module named ...` | Activate `.venv` and run `python -m pip install -r requirements.txt` again. |
| Port `8000` is already in use | Run `python manage.py runserver 8001` and open `http://127.0.0.1:8001/`. |
| Teacher cannot sign in after signup | Ask a project administrator to approve the teacher account. |

## 🚀 ROADMAP

Planned ideas; scope and timing may change:

- **Email recovery:** configure a production email provider for password-reset messages.
- **Insights:** add richer academic analytics and downloadable reports.
- **Responsive polish:** improve mobile dashboard layouts and accessibility.
- **Developer experience:** expand automated tests and first-run setup guidance.

## 🚀 PRODUCTION & DEPLOYMENT

### Production configuration at a glance

| Setting | What it controls |
|---|---|
| `DJANGO_SECRET_KEY` | Private Django signing key; use a unique production value. |
| `DJANGO_DEBUG=false` | Keeps detailed debug pages disabled in production. |
| `DJANGO_ALLOWED_HOSTS` | Permits requests for the deployed hostname. |
| `CSRF_TRUSTED_ORIGINS` | Allows the site's HTTPS origin for protected form requests. |
| `DATABASE_URL` | Connects the app to its PostgreSQL database. |
| `USE_REMOTE_MEDIA=true` | Sends uploaded files to configured object storage. |
| `AWS_STORAGE_BUCKET_NAME`, `AWS_ENDPOINT_URL_S3`, `AWS_REGION` | Identifies the private S3-compatible bucket. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Authenticates the app to object storage; keep these secret. |

See `.env.example` for variable names and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for provider-specific details.

The live website runs on Render. Production requires `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, the correct `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, a PostgreSQL `DATABASE_URL`, and private object-storage credentials.

The repository includes a [Developer Guide](DEVELOPER_GUIDE.md) and [Render Procfile](Procfile). Password-reset email delivery requires a configured production email provider and may not work until those settings are added.

## 🧪 QUALITY CHECKS

GitHub Actions installs the project dependencies, checks Django configuration, collects static files, and runs the automated test suite on supported Python versions. The status badge at the top links to the latest workflow results.

## 🔐 SECURITY & PRIVACY

- Never commit `.env`, database URLs, secret keys, or object-storage credentials.
- Use fictional or approved sample data in screenshots and issue reports.
- Enable `DJANGO_DEBUG=true` only for local development.
- Fee and salary workflows are demonstrations, not payment services.

## ❓ FAQ

**Can I visit a dashboard without signing in?** No. Dashboard routes are protected and require the matching account role.

**Is there a shared demo password?** No public demo credentials are included. Register an account or ask the project administrator.

**Will password reset send me an email?** Email delivery depends on a configured production email provider.

**Are fees paid through this site?** No. Fee and salary pages are demonstration workflows only.

**Why is the first live visit slow?** A free Render instance may be asleep after inactivity and needs time to wake up.

## 📚 PROJECT FILES

| Location | Description |
|---|---|
| `college_management_system/` | Django settings and project routing |
| `main_app/` | Application code, templates, and static assets |
| `docs/screenshots/` | Admin, student, and teacher dashboard gallery |
| `docs/` | Redacted college ERP project report |
| `DEVELOPER_GUIDE.md` | Deployment, object storage, and maintenance |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security reporting guidance |
| `LICENSE` | Project license |

## 🤝 CONTRIBUTE

Suggestions and improvements are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), describe your change clearly, and keep private data and secrets out of commits.

## 📄 LICENSE

See [LICENSE](LICENSE) for the terms that apply to this project.

---

<div align="center">

**VELOCITY TECH UNIVERSITY · COLLEGE ERP SYSTEM**

[OPEN LIVE WEBSITE ↗](https://velocity-tech-university.onrender.com) &nbsp;·&nbsp; [EXPLORE SOURCE CODE ↗](https://github.com/Rohitnag2004/College-ERP-System)

</div>
