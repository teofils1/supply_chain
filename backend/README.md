# Supply Chain Tracking System - Backend

Django REST API backend for the supply chain tracking system.

## Features

-   User management with role-based access control
-   JWT authentication
-   Soft delete functionality
-   Email notifications
-   PostgreSQL database

## Development

### Quick Setup

```bash
# Install dependencies
uv install

# Run migrations
uv run python src/manage.py migrate

# Start development server
uv run python src/manage.py runserver
```

### Using Make Commands

We provide a Makefile for common development tasks:

```bash
# Show all available commands
make help

# Development
make install          # Install dependencies
make dev             # Start development server
make migrate         # Apply database migrations
make shell           # Open Django shell

# Code Quality
make lint            # Run linting checks
make format          # Format code with ruff
make fix             # Auto-fix linting issues and format
make test            # Run tests
make check           # Run linting and tests

# Email Testing
make test-email to=your@email.com  # Test email configuration

# Cleanup
make clean           # Remove cache files
```

### Manual Commands

```bash
# Run linting
uv run ruff check src/

# Fix linting issues automatically
uv run ruff check src/ --fix

# Format code
uv run ruff format src/

# Run tests
uv run python src/manage.py test

# Test email functionality
uv run python src/manage.py test_email --to your@email.com
```

## Email Configuration

The system sends invitation emails when creating new users. Configure email
settings in `.env`:

```properties
# For Gmail (requires app-specific password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_specific_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# For development (prints emails to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Code Quality

This project uses **ruff** for linting and formatting:

-   **Linting**: Checks for code quality, imports, and potential bugs
-   **Formatting**: Ensures consistent code style across the project
-   **Auto-fixing**: Many issues can be automatically resolved

The configuration is in `ruff.toml` and includes:

-   Line length: 88 characters
-   Python 3.12 target
-   Import sorting and optimization
-   Bug detection and code simplification
