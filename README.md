# PlayTo Payout Engine

This is my submission for Playto Founding Engineer Challenge 2026.
---

## Features

* **Idempotent payout creation** (safe retries)
* **Concurrency-safe balance updates** using row-level locking
* **Database-enforced invariants** to prevent duplicate payouts
* **Asynchronous processing** via Celery
* **Retry-safe design** (no stuck payouts)
* **Ledger-based balance tracking**

---

## Tech Stack

* Backend: Django + Django REST Framework
* Database: PostgreSQL
* Async Tasks: Celery + Redis
* Testing: pytest / HTTP-based tests

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/playto-payout-engine.git
cd playto-payout-engine/backend
```

---

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup environment variables

Create a `.env` file (optional) or use defaults:

```env
DB_NAME=playto_pay
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
```

---

### 5. Run database migrations

```bash
python manage.py migrate
```

---

### 6. Seed initial data

```bash
python manage.py seed_data
```

This creates:

* merchants
* initial credits

---

### 7. Start Redis

```bash
redis-server
```

---

### 8. Start Celery worker

```bash
celery -A core worker -l info
```

---

### 9. Run the server

```bash
python manage.py runserver
```

---

## Running Tests

### Django / pytest tests

```bash
pytest
```

---

### HTTP-based tests

```bash
python test/idempotency_test.py
python test/concurrency_test.py
```

---

