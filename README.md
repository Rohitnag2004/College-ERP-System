<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=34&pause=900&color=67E8F9&background=0B1020&center=true&vCenter=true&width=950&height=100&lines=VELOCITY+TECH+UNIVERSITY;ACADEMIC+ERP+PLATFORM;ADMIN+%E2%80%A2+TEACHER+%E2%80%A2+STUDENT" alt="Animated Velocity Tech University title" />

### College ERP · Academic Management · Campus Workflows

A role-based college management platform for students, teachers, and administrators.

[![Open Live Website](https://img.shields.io/badge/OPEN%20LIVE%20WEBSITE-velocity--tech--university.onrender.com-22d3ee?style=for-the-badge&logo=render&logoColor=white)](https://velocity-tech-university.onrender.com)

[![Django CI](https://github.com/Rohitnag2004/College-ERP-System/actions/workflows/django.yml/badge.svg)](https://github.com/Rohitnag2004/College-ERP-System/actions/workflows/django.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)

[Live portal](https://velocity-tech-university.onrender.com) · [Source code](https://github.com/Rohitnag2004/College-ERP-System) · [Developer guide](DEVELOPER_GUIDE.md)

</div>

---

## ✦ About the project

**Velocity Tech University ERP** brings academic and administrative tasks into one Django application. Each role has its own protected dashboard and tools. The deployed app uses PostgreSQL on Neon and S3-compatible object storage for uploaded files.

> **Live demo:** [velocity-tech-university.onrender.com](https://velocity-tech-university.onrender.com)
> Render Free services can sleep while idle, so the first page load may take around a minute to wake up.

## ◈ Open a role dashboard

These pages require an account and sign-in. The links do not give access to anyone else's account or data.

| Dashboard | Open |
|---|---|
| Administrator | [Administrator dashboard](https://velocity-tech-university.onrender.com/admin/home/) |
| Teacher | [Teacher dashboard](https://velocity-tech-university.onrender.com/staff/home/) |
| Student | [Student dashboard](https://velocity-tech-university.onrender.com/student/home/) |

[Sign in](https://velocity-tech-university.onrender.com/) · [Student registration](https://velocity-tech-university.onrender.com/register/student/) · [Teacher registration](https://velocity-tech-university.onrender.com/register/teacher/)

Teacher accounts require administrator approval. Administrator accounts are created by an existing administrator.

## ◈ Dashboard preview

<details>
<summary><strong>Administrator dashboard</strong></summary>
<br />
<img src="docs/screenshots/admin-dashboard.png" alt="Administrator dashboard screenshot" width="100%" />
</details>

<details>
<summary><strong>Student dashboard</strong></summary>
<br />
<img src="docs/screenshots/student-dashboard.png" alt="Student dashboard screenshot" width="100%" />
</details>

<details>
<summary><strong>Teacher dashboard</strong></summary>
<br />
<img src="docs/screenshots/teacher-dashboard.png" alt="Teacher dashboard screenshot" width="100%" />
</details>

These are screenshots of the dashboards. They may display account names and sample information.

## ✦ What you can do

- **Administrator:** manage students, teachers, courses, subjects, sessions, approvals, portal availability, and academic operations.
- **Teacher:** take attendance, manage results, review assigned students, share learning resources, and use leave and feedback workflows.
- **Student:** view attendance and results, register for courses, access learning resources, view fees, notices, and library information.
- **Shared services:** role-aware sign-in, notifications, grade cards, course registration, library management, and cloud-backed uploads.

Fee and salary screens are demonstration workflows; they do not process real payments or transfer money.

## ◈ How the pieces fit together

```mermaid
flowchart LR
    Browser[Web browser] --> Django[Django ERP]
    Django --> Auth[Role-based access]
    Django --> Academic[Academic workflows]
    Django --> Admin[Administrative workflows]
    Auth --> DB[(Neon PostgreSQL)]
    Academic --> DB
    Admin --> DB
    Django --> Files[(S3-compatible object storage)]
    Django --> Static[WhiteNoise static files]
```

## ✦ Technology

| Tool | Used for |
|---|---|
| Python 3.12+ and Django 5.2 | Application and server-side pages |
| PostgreSQL / Neon | User, course, and academic records |
| Neon Object Storage / S3-compatible storage | Uploaded profile images and learning resources |
| Gunicorn and WhiteNoise | Production application and static files |
| GitHub Actions | Automated Django checks and tests |
| Render | Live web service |

## 🚀 Run it on your laptop (beginner guide)

You will need **Python 3.12+**, **Git**, and a PostgreSQL database URL. You can use your own PostgreSQL or Neon database. Keep your database credentials private. For local development, uploaded files can stay on your laptop; you do not need object-storage credentials.

### 1. Install the tools

- Install Python from [python.org](https://www.python.org/downloads/) and enable **Add Python to PATH** during setup.
- Install Git from [git-scm.com](https://git-scm.com/downloads).
- Have a PostgreSQL database ready and keep its connection URL for step 6.

### 2. Download the project

Open **PowerShell** and run:

```powershell
git clone https://github.com/Rohitnag2004/College-ERP-System.git
cd College-ERP-System
```

### 3. Create and activate a Python environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python directly instead: `.\.venv\Scripts\python.exe`.

### 4. Install project packages

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Create your local settings file

```powershell
Copy-Item .env.example .env
notepad .env
```

In `.env`, add your own values. For local-only development, use settings like these:

```dotenv
DJANGO_SECRET_KEY=put-a-long-random-local-key-here
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_HOST/YOUR_DATABASE
USE_REMOTE_MEDIA=false
```

Replace the database URL with your own PostgreSQL connection string. Keep `.env` on your computer; **never upload it to GitHub**. `DJANGO_DEBUG=true` is for local development only.

### 6. Prepare the database and start the site

```powershell
python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser. Register a student or teacher account from the site. A teacher account must be approved by an administrator before it can sign in. The repository does not provide public demo passwords.

### Common first-run issue

If Django says `DATABASE_URL` is missing or invalid, reopen `.env`, check that the URL points to a working PostgreSQL database, save the file, and retry. Do not paste database passwords or secret values into public issues or screenshots.

## ◈ Planned updates

These are ideas for future work; timing may change:

- Configure reliable password-reset email delivery with an email provider.
- Add richer academic analytics and downloadable reports.
- Improve mobile layouts and dashboard accessibility.
- Expand automated tests and developer setup guidance.

## 🚀 Deployment notes

The live site runs on Render. Production needs `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, the correct `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, a PostgreSQL `DATABASE_URL`, and configured private object storage. Do not use the local `.env` values in production.

The repository includes a [Developer Guide](DEVELOPER_GUIDE.md) and a [Render Procfile](Procfile). Password-reset email delivery needs valid production email-provider settings; it may not work until those are configured.

## 🔐 Security and privacy

- Never commit `.env`, database URLs, secret keys, or object-storage credentials.
- Use fictional or approved demo data in screenshots and issue reports.
- Use `DJANGO_DEBUG=true` only on your own local machine.
- Fee and teacher-salary workflows are demonstrations, not payment services.

## 📚 Project files

| File or folder | Purpose |
|---|---|
| `college_management_system/` | Django settings and project routing |
| `main_app/` | Application code, pages, and static assets |
| `docs/screenshots/` | Dashboard screenshots |
| `docs/` | Redacted college ERP project report |
| `DEVELOPER_GUIDE.md` | Deployment, storage, and maintenance |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security reporting guidance |
| `LICENSE` | Project license |

## 🤝 Contributions

Ideas, bug reports, and code improvements are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), describe the change clearly, and never include private user data or secrets.

## 📄 License

See [LICENSE](LICENSE) for the terms that apply to this project.

---

<div align="center">

**Velocity Tech University · College ERP System**
[Visit the live website](https://velocity-tech-university.onrender.com) · [Explore the GitHub repository](https://github.com/Rohitnag2004/College-ERP-System)

</div>
