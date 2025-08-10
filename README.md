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

### Development Tips

- Frontend proxies `/api` requests to the backend for seamless local development.
- Use Django admin to manage users and data.
- Update frontend routes in `src/app/app.routes.ts` for new pages.
- See `src/app/features` for routed Angular components.

