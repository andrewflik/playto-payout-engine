# PlayTo Payout Engine

This is my submission for Playto Founding Engineer Challenge 2026.

---

## Branches

- **main**: Fully functional with Celery for async payout processing. Use for local development and testing.
- **dev**: Deployment-ready version that processes payouts synchronously to avoid Celery/Redis setup. Used for production deployment where background workers are not available.

---

## Features

* Idempotent payout creation (safe retries)
* Concurrency-safe balance updates (`select_for_update`)
* Database-level guarantees (no duplicate payouts)
* Async processing with Celery
* Clean retry model (no stuck payouts)
* Simple frontend dashboard for interaction

---

## Tech Stack

### Backend

* Django + DRF
* PostgreSQL
* Celery + Redis

### Frontend

* React
* Tailwind CSS

---

## ⚙️ Backend Setup

**Note**: This setup is for the `main` branch. For deployment, use the `dev` branch which skips Celery.

### 1. Clone repo

```bash
git clone https://github.com/your-username/playto-payout-engine.git
cd playto-payout-engine/backend
```

---

### 2. Virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure DB

Update `.env` or use defaults:

```env
DB_NAME=playto_pay
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
```

---

### 5. Migrate

```bash
python manage.py migrate
```

---

### 6. Seed data

```bash
python manage.py seed
```

---

### 7. Start services

```bash
redis-server
celery -A core worker -l info
python manage.py runserver
```

---

## Frontend Setup

```bash
cd ../frontend
```

### 1. Install dependencies

```bash
npm install
```

---

### 2. Start frontend

```bash
npm run dev
```

(or `npm start` depending on setup)

---

### 3. Open app

```text
http://localhost:5173
```

---

## Connecting Frontend → Backend

Make sure your frontend is hitting:

```text
http://127.0.0.1:8000/api/v1/payouts/
```

If needed, update:

```js
// example
const API_BASE = "http://127.0.0.1:8000/api/v1/payouts/";
```

---

## Testing

### Backend tests

```bash
pytest
```

---

### HTTP tests

```bash
python test/idempotency_test.py
python test/concurrency_test.py
```

---
