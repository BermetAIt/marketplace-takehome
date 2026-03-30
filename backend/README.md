# Marketplace backend (FastAPI)

Backend for the take-home marketplace: JWT auth (access + refresh), listings with moderation and dynamic JSON attributes, media uploads, favorites, messaging with attachments, notifications, reports, mock payments and promotions, wallet mock top-up, admin dashboard and audit logs.

## Prerequisites

- Python 3.11+
- MySQL 8+ (or compatible)

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy env.example .env            # edit MYSQL_* and SECRET_KEY
```

Create database `marketplace` (or set `MYSQL_DATABASE` in `.env`).

### First-time / schema changes

`app.main` calls `create_all` on startup; it does **not** migrate existing tables. If you have an old schema or stray tables (for example legacy `promotions`), run a full dev reset (destructive):

```powershell
$env:ALLOW_RESET_DEV_DB="1"
python scripts/reset_dev_db.py
python scripts/seed_demo.py
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: `http://127.0.0.1:8000/docs`
- Uploads are served at `/uploads/...` (see `UPLOAD_DIR`)

## Demo credentials (after `seed_demo.py`)

- Admin: `admin@example.com` / `Admin12345!`

## Main route groups

| Prefix | Purpose |
|--------|---------|
| `/auth` | Register, login, refresh, logout, forgot/reset password, change password |
| `/users` | Profile, avatar upload |
| `/public/users` | Public seller profile + active listing count |
| `/categories` | List categories; create requires admin |
| `/listings` | CRUD, browse, `GET /me`, `GET /owner/{id}` |
| `/listings/{id}/images` | Listing images (see `listing_media` router) |
| `/favorites` | Favorites CRUD |
| `/conversations` | Threads + messages (multipart: text + files) |
| `/api/attachments/{id}/download` | Secure attachment download |
| `/notifications` | In-app notifications |
| `/reports` | User reports |
| `/payments` | Initiate mock payment, `mock-confirm`, history, wallet mock top-up |
| `/promotion-packages` | Active packages |
| `/user-promotions` | Purchased promotions for current user |
| `/admin` | Dashboard, users, listings moderation, reports, payments, audit logs |

## Mobile / admin clients

- Send `Authorization: Bearer <access_token>` on protected routes.
- Login returns `access_token` and `refresh_token`; call `POST /auth/refresh` with the refresh body, then `POST /auth/logout` with refresh token to revoke.

## Notes

- Password reset emails are not sent; in `DEBUG=true`, `forgot-password` may return a `debug_reset_token` for testing.
- Payments use a **mock** provider: `POST /payments/{id}/mock-confirm` after `initiate`.
- For production, replace local file storage with object storage and add Alembic (or another migration tool) instead of only `create_all`.
