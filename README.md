# Custom Auth + RBAC Demo (Django + DRF)

A minimal backend with **custom JWT authentication** and a **role-based access control (RBAC)** system that distinguishes **own** vs **all** access per business element.

## API Docs for some endpoints (Postman, just to show I'm familiar with it)

**Docs:** https://documenter.getpostman.com/view/37281446/2sB3WjzjEp  

## Features

- **Auth (JWT)**: register, login, logout, update profile, soft delete account.
- **Custom JWT middleware** sets the authenticated user on the underlying Django request before views.
- **RBAC**:
  - Tables: `roles`, `business_elements`, `access_rules`.
  - Per (role × element) flags: read, read_all, create, update, update_all, delete, delete_all.
  - Superusers bypass checks. Admin role gated by `IsAdminRole`.
- **Admin RBAC API**: `/api/rbac/roles/`, `/api/rbac/elements/`, `/api/rbac/rules/` (CRUD by admins).
- **Mock business endpoints**: `/api/mock/items/` with full 401/403 behavior using RBAC rules.


## Project Structure
```text
├─ core/
│ ├─ init.py
│ ├─ settings.py # ENV-based DB toggle (SQLite/Postgres), DRF, LOGGING
│ ├─ urls.py # mounts /api/auth, /api/rbac, /api/mock, /admin
│ ├─ logging_context.py # request-scoped logging context (rid/uid/path/method)
│ └─ middleware.py # RequestContextMiddleware (sets request_id etc.)
│
├─ accounts/
│ ├─ init.py
│ ├─ models.py # Custom User model (email auth), M2M to Role
│ ├─ serializers.py # Register/Login/UserMe serializers
│ ├─ views.py # Register, Login, Refresh, Logout, Me
│ ├─ urls.py # /api/auth/*
│ └─ migrations/
│ └─ 0001_initial.py
│
├─ authn/
│ ├─ init.py
│ ├─ jwt.py # make_jwt / verify_jwt
│ ├─ middleware.py # JWTAuthMiddleware (sets request.user from Bearer)
│ ├─ drf_auth.py # DRF Authentication class (sets request.user)
│ ├─ models.py # RefreshToken (server-stored, rotation)
│ ├─ services.py # issue/rotate/revoke refresh tokens
│ └─ admin.py # (optional) RefreshToken admin
│
├─ accesscontrol/
│ ├─ init.py
│ ├─ models.py # Role, BusinessElement, AccessRule (own vs all)
│ ├─ services.py # has_permission(user, element, action, owner_id)
│ ├─ permissions.py # IsAdminRole (superuser or role 'admin')
│ ├─ views.py # Admin RBAC viewsets
│ ├─ urls.py # /api/rbac/*
│ ├─ migrations/
│ │ └─ 0001_initial.py
│ └─ management/
│ └─ commands/
│ └─ seed_demo.py # Idempotent seeder (roles/elements/rules/users/items)
│
├─ mockbiz/
│ ├─ init.py
│ └─ views.py # /api/mock/items/ (in-memory items; RBAC enforced)
│
├─ manage.py
├─ requirements.txt
├─ README.md
├─ .env # local env (JWT_SECRET, USE_SQLITE, LOG_LEVEL, etc.)
├─ .gitignore # ignores .venv/, db.sqlite3, pycache/, etc.
│
├─ docker-compose.yml # (optional) Docker dev; API (and optionally DB)
├─ docker-compose.pg.yml # (optional) Add Postgres when needed
├─ Dockerfile # Python image + deps
```
## Local Run

```bash
# 1) Create a virtualenv (recommended)
python -m venv .venv && . .venv/bin/activate
# 2) Install deps
pip install -r requirements.txt
# 3) Migrate
python manage.py migrate
# 4) (Optional) Create superuser for admin
python manage.py createsuperuser --email admin@example.com
# 5) added the seeds
python manage.py seed_demo --with-users --with-items --admin-email admin@example.com --admin-password 'YOUR PASSWORD'

# 6) Run
python manage.py runserver
```
## Docker Run

```bash
docker compose up --build

#create superuser
docker compose exec api python manage.py createsuperuser
```

## Some of the Endpoints

### Auth
- **POST** `/api/auth/register/`  
  Body (JSON): `{"email","password","password2","first_name","last_name"}`
  
- **POST** `/api/auth/login/`  
  Body (JSON): `{"email","password"}`  
  Returns: `{"access": "<jwt>", "refresh": "<token>", "user": {...}}`

- **POST** `/api/auth/refresh/`  
  Body (JSON): `{"refresh": "<token>"}`  
  Returns (rotated): `{"access": "<new_jwt>", "refresh": "<new_token>"}`

- **POST** `/api/auth/logout/`  
  Body (JSON, optional): `{"refresh": "<token>"}`  (revokes this refresh if provided)

- **GET** `/api/auth/me/`  
  Auth: `Authorization: Bearer <access>`

- **PATCH** `/api/auth/me/`  
  Auth: `Authorization: Bearer <access>`  
  Body: partial profile fields

- **DELETE** `/api/auth/me/`  
  Auth: `Authorization: Bearer <access>`  
  Effect: soft delete (`is_active = false`)