# Supply Chain Tracking System

A full-stack application for end-to-end supply chain tracking, leveraging blockchain anchoring for tamper-evident provenance.

## Tech Stack

**Frontend**

- Angular 20 (standalone components)
- PrimeNG 20 UI (`@primeuix/themes` Aura preset)
- Tailwind CSS v4 (`tailwindcss-primeui`)
- Vite dev server

**Backend**

- Django 5 + Django REST Framework
- PostgreSQL (via psycopg)
- Simple JWT authentication
- Blockchain integration via Web3

## Features

- **Authentication:** JWT-based login, route guards, and token refresh.
- **Products:** List, detail, and manage products (SKU, lot, serial).
- **Shipments:** Track shipments and their associated products.
- **Events:** Record checkpoints/events (location, status, timestamp, signer).
- **Blockchain Anchoring:** Critical events are hashed and anchored on-chain for integrity verification.
- **Role-based Access:** Operator, auditor, and admin roles.

## Getting Started

### Prerequisites

- **Python 3.12+** - Backend runtime
- **Node.js 18+** - Frontend build tooling
- **PostgreSQL 16+** - Database
- **Docker & Docker Compose** - For RabbitMQ and Redis (optional)

### Quick Start (From Scratch)

#### 1. Clone and Setup Infrastructure

```bash
# Start required services (PostgreSQL, RabbitMQ, Redis)
docker-compose up -d
```

This starts:

- PostgreSQL on port 5432
- RabbitMQ on ports 5672 (AMQP) and 15672 (Management UI)
- Redis on port 6379

#### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Navigate to src directory
cd src

# Run database migrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser

# Start Django development server
python manage.py runserver
```

The API runs at [http://127.0.0.1:8000](http://127.0.0.1:8000).

#### 3. Start Celery Worker (for Notifications)

In a **new terminal**:

```bash
cd backend
source .venv/bin/activate
celery -A api worker -l info --pool=solo
```

This starts the Celery worker for processing async notification tasks.

#### 4. Frontend Setup

In a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app runs at [http://localhost:4200](http://localhost:4200).

#### 5. Access the Application

- **Frontend**: http://localhost:4200
- **Backend API**: http://127.0.0.1:8000/api/
- **Django Admin**: http://127.0.0.1:8000/admin/
- **Swagger API Docs**: http://127.0.0.1:8000/api/docs/
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### Initial Setup & Configuration

#### Create Test Data

```bash
cd backend/src
python manage.py shell

# In the Python shell:
from supplychain.models import User
from django.contrib.auth.models import Group

# Create roles
operator_group, _ = Group.objects.get_or_create(name='operator')
auditor_group, _ = Group.objects.get_or_create(name='auditor')

# Create test users
operator = User.objects.create_user(
    username='operator',
    email='operator@example.com',
    password='operator123'
)
operator.groups.add(operator_group)

auditor = User.objects.create_user(
    username='auditor',
    email='auditor@example.com',
    password='auditor123'
)
auditor.groups.add(auditor_group)
```

#### Environment Variables

Create a `.env` file in `backend/src/` (optional, has defaults):

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://supply_chain_user:your_password@localhost:5432/supply_chain_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

# Email settings (for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
LOG_JSON=False
LOG_TO_FILE=True

# Blockchain (for future integration)
BLOCKCHAIN_PROVIDER_URL=http://localhost:8545
BLOCKCHAIN_PRIVATE_KEY=your-private-key
```

### Running in Production

```bash
# Frontend build
cd frontend
npm run build

# Backend with Gunicorn
cd backend
pip install gunicorn
gunicorn api.wsgi:application --bind 0.0.0.0:8000

# Celery worker (background)
celery -A api worker -l info --pool=solo --detach

# Celery beat (for periodic tasks)
celery -A api beat -l info --detach
```

### Stopping Services

```bash
# Stop Docker services
docker-compose down

# Stop development servers with Ctrl+C in each terminal
```

### API Documentation

Interactive API documentation is available via drf-spectacular:

- **Swagger UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) - Interactive API explorer with "Try it out" functionality
- **ReDoc**: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/) - Clean, responsive API documentation
- **OpenAPI Schema**: [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/) - Raw OpenAPI 3.0 schema (JSON)

The documentation includes:

- All API endpoints with request/response examples
- Authentication requirements (JWT Bearer tokens)
- Query parameters and filtering options
- Detailed model schemas
- Try-it-out functionality in Swagger UI

### Development Tips

- Frontend proxies `/api` requests to the backend for seamless local development.
- Use Django admin to manage users and data.
- Update frontend routes in `src/app/app.routes.ts` for new pages.
- See `src/app/features` for routed Angular components.
- Use the Swagger UI to test API endpoints and understand request/response formats.
