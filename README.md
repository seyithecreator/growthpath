# GrowthPath — Intelligent Decision-Support System
## Personal Growth & Skill Development Platform

A full-stack Django 4.2 web application for Nigerian university students to monitor
performance, evaluate skills, set priorities, and receive AI-driven recommendations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Django 4.2 |
| REST API | Django REST Framework 3.15 |
| Database | PostgreSQL 15 |
| ML Engine | Scikit-learn 1.4, Pandas 2.2, NumPy 1.26 |
| Task Queue | Celery 5.4 + Redis |
| Frontend | Bootstrap 5.3, Chart.js 4.4, Vanilla JS |
| Auth | Django Auth + DRF Token Auth |
| Hosting | Gunicorn + WhiteNoise |

---

## Project Structure

```
growthpath/
├── growthpath/
│   ├── settings.py          # Django config (PostgreSQL, Redis, ML weights)
│   ├── urls.py              # Root URL dispatcher
│   ├── celery_tasks.py      # Async: snapshots, recommendations, streaks
│   └── wsgi.py
│
├── apps/
│   ├── accounts/            # Custom User model + achievements
│   ├── goals/               # Goal + Milestone tracking
│   ├── skills/              # Skill domains + score history
│   ├── activities/          # Activity logs + productivity snapshots
│   ├── priorities/          # Priority ranking algorithm engine
│   └── recommendations/     # Scikit-learn recommendation engine
│
├── templates/
│   ├── base.html            # Mobile-first Bootstrap 5 shell
│   ├── dashboard/index.html # Main dashboard
│   └── goals/ skills/ ...   # Feature templates
│
├── static/                  # CSS, JS, images
├── requirements.txt
└── manage.py
```

---

## Setup Instructions

### 1. Clone and create virtual environment

```bash
git clone https://github.com/yourusername/growthpath.git
cd growthpath
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=growthpath_db
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/0

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:8000
```

### 4. Create PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE growthpath_db;
\q
```

### 5. Run migrations

```bash
python manage.py makemigrations accounts goals skills activities priorities recommendations
python manage.py migrate
```

### 6. Create superuser

```bash
python manage.py createsuperuser
```

### 7. Seed sample data (Nigerian university students)

```bash
python manage.py seed_data
# Creates 5 sample users: tunde_a, chioma_o, emeka_n, fatima_b, seun_o
# Password for all: testpass123
```

### 8. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 9. Start the development server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Starting Celery (for async tasks)

In a separate terminal:

```bash
# Worker
celery -A growthpath worker -l info

# Beat scheduler (for periodic tasks)
celery -A growthpath beat -l info
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login/` | Obtain auth token |
| GET | `/api/v1/auth/me/` | Current user profile |
| GET/POST | `/api/v1/goals/` | List / create goals |
| PATCH | `/api/v1/goals/{id}/update_progress/` | Update goal progress |
| POST | `/api/v1/goals/{id}/complete/` | Mark goal complete |
| GET/POST | `/api/v1/skills/` | List / create skills |
| POST | `/api/v1/skills/{id}/update_score/` | Update skill score |
| GET | `/api/v1/skills/radar_data/` | Radar chart data |
| GET/POST | `/api/v1/activities/` | Activity log CRUD |
| GET | `/api/v1/priorities/` | Ranked priority list |
| GET | `/api/v1/recommendations/` | Current recommendations |
| POST | `/api/v1/recommendations/generate/` | Trigger ML generation |

---

## Priority Algorithm

```
Priority Score = (0.40 × Deadline Urgency)
               + (0.35 × Goal Importance)
               + (0.25 × Historical Completion Rate)
```

- **Deadline Urgency**: Exponential decay — `100 × e^(−0.05 × days_remaining)`
- **Goal Importance**: High=90, Medium=55, Low=20
- **Completion Rate**: Derived from activity log history via Pandas

---

## Recommendation Engine Layers

1. **Rule-based heuristics** (always active): deadline alerts, skill gaps, habit gaps
2. **Random Forest classifier** (≥3 activity logs): predicts peak productivity hour
3. **Cosine similarity** (≥3 activity logs): peer-based skill recommendations

---

## Running Tests

```bash
python manage.py test apps.goals apps.skills apps.activities apps.priorities apps.recommendations
```

---

## Deployment (Production)

```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Use gunicorn
gunicorn growthpath.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Serve with Nginx reverse proxy
# Static files served by WhiteNoise
```

---

## Research Context

This system was evaluated with a sample of Nigerian university students, measuring:
- Decision-making quality improvements vs. traditional tracking methods
- Self-reported productivity scores over 4-week periods
- Goal completion rates before/after system adoption
- Skill score trajectory across tracked domains

Reference: McKinney, W. (2017). *Python for Data Analysis*. O'Reilly Media.
