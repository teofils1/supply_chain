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

## Improvements & Roadmap

### 2. API Documentation

✅ **Implemented**: API documentation with Swagger/OpenAPI via drf-spectacular

### 3. Data Validation

✅ **Implemented**: Comprehensive custom validators including:

- ✅ Expiry dates validation (must be > manufacturing_date)
- ✅ Quantity constraints (available_quantity ≤ quantity_produced)
- ✅ Tracking number format validation (alphanumeric with hyphens/underscores, 5-50 chars)
- ✅ Temperature range validations (-100°C to 100°C with min < max)
- ✅ GTIN format validation with check digit verification
- ✅ Lot number and serial number format validation
- ✅ Humidity range validation (0-100%)
- ✅ Date relationship validation (shipping/delivery dates)

### 4. Error Handling & Logging

✅ **Implemented**: Comprehensive error handling and logging system including:

- ✅ Centralized exception handler with consistent error response format
- ✅ Custom domain-specific exception classes (SupplyChainException, BlockchainException, etc.)
- ✅ Structured logging with structlog (JSON for production, pretty console for development)
- ✅ Request/response logging middleware for audit trails
- ✅ Separate log files (app.log, error.log, audit.log) with rotation
- ✅ Request ID tracking for correlation across services
- ✅ Configurable via environment variables (LOG_LEVEL, LOG_JSON, LOG_TO_FILE)

### 5. Performance Optimizations

✅ **Implemented**: Comprehensive performance optimizations including:

- ✅ Database indexes on frequently queried fields (tracking_number, serial_number, lot_number, gtin, status, dates)
- ✅ Pagination on all list endpoints with configurable page size (default 25, max 100)
- ✅ Custom pagination classes (StandardResultsPagination, LargeResultsPagination, SmallResultsPagination)
- ✅ select_related and prefetch_related on all list/detail views to eliminate N+1 queries
- ✅ Redis caching support with automatic fallback to local memory cache
- ✅ Caching utilities with decorators for API response caching
- ✅ Configurable via environment variables (REDIS_URL, CACHE_TIMEOUT, API_PAGE_SIZE)

### 6. Advanced Analytics Dashboard

- Supply chain KPIs (on-time delivery %, damage rate)
- Batch yield analysis
- Carrier performance metrics
- Temperature excursion trends
- Predictive analytics for demand forecasting

### 7. Document Management

✅ **Implemented**: Comprehensive document management system including:

- ✅ Upload/attach documents to products, batches, shipments, and packs
- ✅ PDF generation for shipping labels, packing lists, and Certificates of Analysis
- ✅ Professional PDF templates using WeasyPrint (HTML to PDF conversion)
- ✅ Document versioning and version control
- ✅ Document metadata tracking (title, category, file type, size, hash)
- ✅ Generic foreign key relations for flexible entity association
- ✅ Document download and file serving
- ✅ Frontend UI for document management with upload, download, and deletion
- ✅ One-click PDF generation from shipment and batch detail pages
- ✅ Automatic document attachment or direct download options

**Available PDF Documents:**

- Shipping Labels (4"×6" format with barcode, addresses, carrier info)
- Packing Lists (A4 format with shipment contents table)
- Certificates of Analysis (CoA) for batches with QA signatures

### 8. Notifications System

✅ **Implemented**: Real-time notification system including:

- ✅ Celery + RabbitMQ for async task processing
- ✅ Email notifications for critical events
- ✅ NotificationRule model for user-configurable alert rules
- ✅ NotificationLog model for tracking all notifications
- ✅ 9 REST API endpoints for notification management
- ✅ Event-driven notifications (auto-triggered on recalls, alerts, errors)
- ✅ Notification severity levels (critical, high, medium, low, info)
- ✅ Multiple channels (email, SMS, webhook) - email fully implemented
- ✅ Escalation system for unacknowledged critical notifications
- ✅ Frontend notification bell with unread count badge
- ✅ Notification list page with filtering (status, channel, read/unread)
- ✅ Notification settings page for rule management
- ✅ Mark as read/acknowledge functionality
- ✅ Professional HTML email templates for different severity levels

**How to Use:**

1. Navigate to **Notification Settings** to create notification rules
2. Select event types (e.g., product_recalled, temperature_alert)
3. Choose severity levels to monitor (critical, high, etc.)
4. Configure channels (email active, SMS/webhook ready for integration)
5. Notifications appear in the bell icon when events occur
6. Click bell to view recent notifications or navigate to full list

