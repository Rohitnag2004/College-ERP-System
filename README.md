<!-- Animated Project Header -->

<p align="center">
  <img
    src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=28&pause=1000&color=58A6FF&center=true&vCenter=true&width=750&lines=Velocity+Tech+University;College+ERP+%7C+Django+%7C+PostgreSQL;Smarter+Academic+Management"
    alt="Animated Velocity Tech University heading"
  />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Django-Powered-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Database-Neon_PostgreSQL-00E599?style=for-the-badge&logo=postgresql&logoColor=black" alt="Neon PostgreSQL" />
</p>

<p align="center">
  <a href="https://github.com/Rohitnag2004/College-ERP-System">
    <img src="https://img.shields.io/badge/Explore-Repository-238636?style=for-the-badge&logo=github&logoColor=white" alt="Explore Repository" />
  </a>
</p>

<p align="center">
  <i>One platform. Three roles. Smarter academic workflows.</i>
</p>

---

### 🎓 About the Project

Velocity Tech University is a Django-based College ERP designed to bring student services, faculty workflows, and academic administration together in one centralized platform.

Built with Python, Django, Neon PostgreSQL, and S3-compatible object storage.

# 🎓 Velocity Tech University
### College ERP & Academic Management System

<p align="center">
  A modern, Django-powered platform designed to simplify college administration and academic workflows.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Storage-S3--Compatible-orange?style=for-the-badge&logo=amazons3&logoColor=white" alt="Object Storage" />
</p>

<p align="center">
  <strong>Admin Dashboard · Faculty Management · Student Services · Academic Records</strong>
</p>

---

## 📌 Overview

**Velocity Tech University** is a Django-based College Enterprise Resource Planning (ERP) system that brings essential academic and administrative operations into one centralized platform.

The system supports role-based workflows for administrators, teachers, and students, helping manage academic records, course applications, attendance, results, fee records, notices, assignments, and learning resources.

Built with **Django, Neon PostgreSQL, and S3-compatible object storage**, the project separates application data from uploaded media to support cloud deployment.

## ✨ Key Features

| Module | Capabilities |
|---|---|
| 🔐 Authentication | Role-aware sign-in and student/teacher registration |
| 🛡️ Administration | User management, teacher approval, and academic administration |
| 🎓 Student Services | Student records and course applications |
| 👨‍🏫 Faculty Management | Teacher accounts and academic workflows |
| 📚 Learning Resources | Assignments, notices, and private learning materials |
| 📊 Academic Records | Attendance and examination results |
| 💳 Fee Management | Demo fee workflows and fee records |
| ⚙️ System Controls | Independent admin-controlled student and teacher maintenance switches |
| 🔎 User Experience | Responsive dashboards, search, and pagination |
| ⏱️ Session Management | Five-minute idle session expiry |

> **Note:** Fee and teacher salary workflows are demonstrational. The application does not transfer money.

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Django | Web framework and application logic |
| PostgreSQL | Relational database |
| Neon | Hosted PostgreSQL and S3-compatible object storage |
| WhiteNoise | Static file serving |
| Gunicorn | Production WSGI application server |
| Git & GitHub | Version control and source code hosting |

## 🏗️ Architecture

```text
                    ┌────────────────────────┐
                    │      Web Browser       │
                    │ Admin / Teacher /      │
                    │       Student          │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │    Django ERP App      │
                    │ Authentication, Views, │
                    │ Academic Workflows     │
                    └───────┬────────┬───────┘
                            │        │
                   ┌────────▼───┐  ┌─▼────────────────┐
                   │   Neon     │  │  S3-Compatible   │
                   │ PostgreSQL │  │  Object Storage  │
                   │ Application│  │ Photos & Uploads │
                   │   Records  │  │                  │
                   └────────────┘  └──────────────────┘
```

**Storage design**
- **Database:** Application records are stored in Neon PostgreSQL.
- **Uploaded media:** Production uploads use a private S3-compatible object-storage bucket.
- **Static assets:** Static files are collected during deployment and served using WhiteNoise.
- **Credentials:** Database and storage credentials belong in environment variables, never in Git.

## 🚀 Getting Started

Follow these steps to run the project locally.

### Prerequisites

- Python 3.10 or later
- Git
- Access to a PostgreSQL database, such as Neon
- Environment variables configured for the application

### 1. Clone the Repository

```bash
git clone https://github.com/Rohitnag2004/College-ERP-System.git
cd College-ERP-System
```

### 2. Create a Virtual Environment

**Windows — PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, consult the Python documentation or activate the environment using your preferred terminal.

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update the values in `.env` for your own development environment.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django application secret |
| `DJANGO_DEBUG` | Enable or disable debug mode |
| `DJANGO_ALLOWED_HOSTS` | Allowed hostnames |
| `DATABASE_URL` | PostgreSQL connection URL |
| `USE_REMOTE_MEDIA` | Enable S3-compatible media storage |
| `AWS_STORAGE_BUCKET_NAME` | Object-storage bucket name |
| `AWS_ACCESS_KEY_ID` | Object-storage access key |
| `AWS_SECRET_ACCESS_KEY` | Object-storage secret key |
| `AWS_ENDPOINT_URL_S3` | Optional S3-compatible endpoint |
| `AWS_REGION` | Object-storage region |

For local development, set `DJANGO_DEBUG=true` and configure a new development secret key and a valid database URL.

For remote media uploads, set `USE_REMOTE_MEDIA=true` and provide the required storage credentials.

**Security:** Never commit `.env` or publish production credentials. The `.env.example` file should contain placeholders only.

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

**http://127.0.0.1:8000/**

> No default account passwords or production secrets are included in the source repository. Use the application's registration and administrative setup workflows to configure accounts.

## ☁️ Deployment

The project can be deployed to a Django-compatible hosting provider, such as Render, with Neon PostgreSQL and private S3-compatible object storage.

### Production Checklist

- [ ] Configure `DJANGO_SECRET_KEY` with a secure, unique value.
- [ ] Set `DJANGO_DEBUG=false`.
- [ ] Configure `DJANGO_ALLOWED_HOSTS` for the deployed hostname.
- [ ] Configure `CSRF_TRUSTED_ORIGINS` for the HTTPS application URL.
- [ ] Set `DATABASE_URL` to the production PostgreSQL connection URL.
- [ ] Configure the required private object-storage credentials.
- [ ] Configure SMTP settings if password-reset emails are required.
- [ ] Apply database migrations.
- [ ] Collect static files.
- [ ] Verify login, registration, dashboards, database access, and media uploads.

Run the following commands during deployment when appropriate:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

The repository's `Procfile` defines the Gunicorn startup command. Configure the hosting provider to use the repository's actual build and start configuration.

**Important:** Production requires remote media storage according to the current application settings. Configure the bucket and credentials before launching the service.

For detailed architecture, object-storage configuration, maintenance procedures, and safe updates, see **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**.

## 🖼️ Screenshots

Add screenshots of the actual application here to help visitors understand the interface.

Suggested screenshots:
- Admin Dashboard
- Student Dashboard
- Teacher Dashboard
- Course and Attendance Management
- Results and Fee Management

Store approved screenshots in a repository folder such as `docs/screenshots/`, then embed them using relative Markdown paths.

## 🔒 Security

- Keep environment files and production credentials out of Git.
- Use HTTPS and secure production settings.
- Use private object storage for uploaded media.
- Do not publish real student records, personal information, or account credentials in screenshots.
- Review configuration changes before deploying to production.

For security-related disclosures, follow the instructions in [SECURITY.md](SECURITY.md), if available.

## 📁 Project Documentation

- **[README](README.md)** — Project overview and setup instructions
- **[Developer Guide](DEVELOPER_GUIDE.md)** — Architecture, storage, deployment, and maintenance
- **[Project Report](docs/College-ERP-Project-Report-Redacted.pdf)** — Project documentation
- **[License](LICENSE)** — Licensing terms

## 🛣️ Future Improvements

Potential enhancements for future development:

- Automated email notifications and password recovery
- Expanded academic analytics and reporting
- Additional testing and deployment automation
- Improved documentation with real application screenshots

These are potential improvements, not claims about features already implemented.

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Submit a pull request describing the changes.

Please review the project's existing contribution guidelines before submitting changes.

## 📄 License

This project is distributed under the license specified in the [LICENSE](LICENSE) file.

---

<p align="center">
  Built with Python and Django for academic and administrative management.
</p>

<p align="center">
  <a href="https://github.com/Rohitnag2004/College-ERP-System">View Repository</a>
</p>
