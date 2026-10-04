# AutoDrop Engine 🚀

A lightning-fast, zero-admin, headless-style dropshipping e-commerce engine optimized for the Central and Eastern European (CEE) market. Designed to run an automated e-commerce node with minimal resource consumption and zero manual intervention.

---

## 🏛️ Core Philosophy & Automation Pipeline

This project completely eliminates manual administrative overhead by fully robotizing the entire e-commerce lifecycle:
1. **Automated Catalog Ingestion:** Scheduled background workers periodically fetch, normalize, and translate supplier product feeds (XML/CSV/REST API) directly into the local database.
2. **Real-Time Inventory Buffer & Sync:** Hourly inventory polling prevents overselling by applying safety buffers against multi-channel supplier stock fluctuations.
3. **Automated Order Dispatch:** Once a customer completes checkout, the system automatically routes the purchase payload via API to the upstream CEE supplier/fulfillment center (e.g., Webshippy or Matterhorn).
4. **Fiscal Compliance & Invoicing:** Automatically triggers NAV-compliant electronic invoicing via cloud billing APIs upon payment verification.

---

## 🤖 Features & Capabilities

### ✅ Implemented Features
- TODO

### 📋 Roadmap / Planned Features
- TODO

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.12+ / FastAPI | High-performance asynchronous API & routing |
| **Server** | Uvicorn + Apache | Lightweight ASGI runner behind an Apache reverse proxy |
| **Frontend UI** | Jinja2 + Tailwind CSS | Mobile-first server-rendered interface |
| **Interactivity** | HTMX 2.x | Single-page app (SPA) feel with zero client JS build steps |
| **Internationalization** | GNU gettext + Babel | Production-ready localization & message catalogs |
| **ORM & Migrations**| SQLAlchemy 2.0 + Alembic | Unified data layer across dev and production |
| **Databases** | SQLite (Dev/Test) / MySQL (Prod) | Fast local development and isolated in-memory testing |
| **Testing** | Pytest + FastAPI TestClient | Sub-second test execution without browser automation |

---

## 📂 Project Structure

```text
autodrop/
├── alembic/            # Database schema migration scripts
├── changes/            # Architecture design & implementation summaries per PR
├── autodrop/
│   ├── core/           # Configuration, security, database engine, i18n, logging, validation
│   ├── locales/        # PO templates and compiled MO translation catalogs
│   ├── models/         # SQLAlchemy database models (User, Product, etc.)
│   ├── routes/         # FastAPI path operations (auth, profile, etc.)
│   ├── services/       # Domain and business logic (auth, email, user, etc.)
│   ├── static/         # Icons, manifest.json, styles
│   └── templates/      # Jinja2 templates and HTMX partials
│       ├── auth/       # Authentication views
│       ├── emails/     # Email notification templates (HTML + Plaintext)
│       ├── errors/     # Error pages (500 internal server error, etc.)
│       ├── macros/     # Reusable Jinja2 macros (translatable inputs, etc.)
│       └── profile/    # User profile views
├── scripts/            # Helper scripts (git workflow, db migrations, i18n management, test runner)
├── tests/              # Pytest unit and integration test suite
├── alembic.ini         # Alembic migration configuration
├── babel.cfg           # Babel i18n extraction settings
├── ENV.md              # Python development environment setup guide
├── pytest.ini          # Pytest configuration
└── README.md
```

---

## 🚀 Getting Started

### Requirements & Setup
- **Development Setup:** [Create the Python environment](./ENV.md)

### Run Database Migrations
Apply database migrations using Alembic directly or via the helper script:
```bash
./scripts/db_upgrade.sh
# Or directly: alembic upgrade head
```

### Start Development Server
```bash
uvicorn autodrop.main:app --reload --host 127.0.0.1 --port 8000
```

### Run Test Suite
```bash
./scripts/run_tests.sh
# Or directly: pytest
```

---

## 🌐 Internationalization (i18n) Workflow

Manage translation catalogs using the provided helper scripts:

```bash
# Extract translatable strings from Python code & templates and update .po files
./scripts/i18n_update.sh

# Compile catalogs (.po -> .mo) for runtime use
./scripts/i18n_compile.sh

# Initialize a new translation catalog (e.g. ja, de)
./scripts/i18n_init.sh ja
```
