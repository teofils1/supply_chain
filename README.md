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

### Frontend

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm start
```

The app runs at [http://localhost:4200](http://localhost:4200).

3. Build for production:

```bash
npm run build
```

4. Run tests:

```bash
npm test
```

### Backend

1. Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `backend/.env` (see example in `src/api/settings.py`).

4. Run migrations:

```bash
python manage.py migrate
```

5. Start the backend server:

```bash
python manage.py runserver
```

The API runs at [http://127.0.0.1:8000](http://127.0.0.1:8000).

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

Centralized error handling middleware
Structured logging (consider structlog)
Better error messages for API responses
Request/response logging for audit

5. Performance Optimizations
   Add database indexes on frequently queried fields (tracking_number, serial_number, lot_number)
   Implement pagination on all list endpoints
   Add select_related and prefetch_related to reduce N+1 queries
   Consider caching for frequently accessed data (Redis)

6. Advanced Analytics Dashboard
   Supply chain KPIs (on-time delivery %, damage rate)
   Batch yield analysis
   Carrier performance metrics
   Temperature excursion trends
   Predictive analytics for demand forecasting

7. Document Management
   Upload/attach documents to products, batches, shipments
   PDF generation for shipping labels, packing lists, CoAs
   E-signature support for approvals
   Version control for documents

8. Notifications System
   Email/SMS alerts for critical events
   Real-time WebSocket notifications (Django Channels)
   Configurable alert rules per user role
   Escalation workflows

9. Inventory Management
   Warehouse location tracking (bin/shelf)
   Stock level alerts (min/max thresholds)
   Automated reorder suggestions
   Inventory reconciliation tools
   FIFO/FEFO/LIFO picking strategies

10. Advanced Blockchain Features
    Replace mock implementation with real blockchain
    Multi-chain support (Ethereum, Polygon, Hyperledger)
    Smart contracts for automated compliance
    Public verification portal (verify by serial number)

11. Returns Management
    Return request workflow
    RMA (Return Merchandise Authorization)
    Refund/replacement tracking
    Return reason analysis
12. Supplier/Customer Portal
    External user access with limited permissions
    Self-service order tracking
    API keys for integration
