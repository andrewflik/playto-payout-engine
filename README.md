# PayFlow — Payout Engine

A hobby project I built to explore reliable payout processing — idempotency, concurrency safety, and async job queues. Nothing production-critical, just a deep dive into patterns I wanted to understand better.

---

## Branches

- **main**: Full setup with Celery for async payout processing. Use for local development and testing.
- **dev**: Synchronous version — no Celery or Redis required. Easier to spin up quickly.

---

## What I was exploring

- Idempotent payout creation (safe retries without double-processing)
- Concurrency-safe balance updates using `select_for_update`
- Database-level guarantees against duplicate payouts
- Async job processing with Celery + Redis
- Clean retry logic — no stuck or zombie payouts
- A minimal React dashboard to interact with it all

---

## Tech Stack

### Backend
- Django + DRF
- PostgreSQL
- Celery + Redis

### Frontend
- React
- Tailwind CSS

---

## Backend Setup

> For the simpler setup without Celery, switch to the `dev` branch.

### 1. Clone the repo

```bash
git clone https://github.com/your-username/payflow.git
cd payflow/backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Update `.env` or use the defaults:

```env
DB_NAME=payflow
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Seed sample data

```bash
python manage.py seed
```

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
npm install
npm run dev
```

Open at: `http://localhost:5173`

---

## Connecting Frontend → Backend

The frontend expects the API at:

```
http://127.0.0.1:8000/api/v1/payouts/
```

To change it:

```js
const API_BASE = "http://127.0.0.1:8000/api/v1/payouts/";
```

---

## Tests

```bash
# Unit tests
pytest

# Idempotency + concurrency scenarios
python test/idempotency_test.py
python test/concurrency_test.py
```
