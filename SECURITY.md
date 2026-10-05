# Security policy

Velocity Tech University is a Django-based university portal. This repository does not operate a public production service.

## Reporting a vulnerability

Do not publish passwords, Neon connection strings, private student information, or a working exploit in a public issue. Contact the project maintainer privately through the contact channel provided by the project owner. Include the affected URL or file, steps to reproduce, and the impact. Do not test against systems or data that you do not own or have permission to assess.

## Deployment essentials

- Keep `.env` and all production secrets out of version control.
- Use a unique `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, explicit `DJANGO_ALLOWED_HOSTS`, and HTTPS in production.
- Use Neon PostgreSQL over SSL and a least-privilege database role.
- Configure SMTP credentials using environment variables.
- Keep Django and dependencies on supported security releases.
- Use durable, access-controlled media storage for uploaded profile images.
- Back up the database and verify recovery procedures.

Security reports are reviewed by the project owner. This repository does not operate a vulnerability bounty.
