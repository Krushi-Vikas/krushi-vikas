# 🌱 Krushi Vikas (krushi-vikas-dev)

**Krushi Vikas Agri and Watershed Project Management** — a custom Frappe v15 application for managing project themes, goals, objectives, Key Result Indicators (KRE), concept notes, beneficiaries, and field surveys.

---

## 📋 Table of Contents
- [Prerequisites](#-prerequisites)
- [Developer Quick Start](#-developer-quick-start)
- [How to Restore the Demo Database (Optional)](#-how-to-restore-the-demo-database-optional)
- [Running the Development Server](#-running-the-development-server)
- [Default Login Credentials](#-default-login-credentials)
- [Project Directory Architecture](#-project-directory-architecture)
- [Development Workflow](#-development-workflow)
- [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## ⚙️ Prerequisites

Before installing the app, ensure your machine (or WSL 2 / Linux environment) has:
- **Python**: `3.10`, `3.11`, or `3.12`
- **Node.js**: `v18.x` or `v20.x` & **Yarn**: `v1.22+`
- **MariaDB**: `10.6+` (configured with `utf8mb4` character set)
- **Redis**: `v6.0+`
- **Frappe Bench CLI**: `v5.x+` (installed via `pipx install frappe-bench`)

---

## 🚀 Developer Quick Start

Follow these steps to set up and run the app locally:

### 1. Initialize Frappe Bench (if not already created)
```bash
# In your Linux / WSL environment:
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench
```

### 2. Create a Site & Install ERPNext (Optional/Recommended)
```bash
bench new-site frappe.local --admin-password admin
bench get-app erpnext --branch version-15
bench --site frappe.local install-app erpnext
```

### 3. Clone and Link `krushi_vikas`
```bash
# Clone this repository into the bench apps folder:
bench get-app https://github.com/Krushi-Vikas/krushi-vikas-dev.git --branch feature/kushi-vikas-implementation

# Install the app onto your site:
bench --site frappe.local install-app krushi_vikas

# Run migrations to build database tables and sync fixtures:
bench --site frappe.local migrate
```

---

## 💾 How to Restore the Demo Database (Optional)

If you want the exact seed database containing pre-configured concept notes, workflows, and test data:

```bash
cd frappe-bench

# Restore database from the included backup:
bench --site frappe.local restore apps/krushi_vikas/backups/20260816_234450-dev_localhost-database.sql.gz

# Run migrate to ensure schema integrity:
bench --site frappe.local migrate
```

---

## 🖥️ Running the Development Server

Start the multi-process bench server (Redis, Web WSGI, Socket.IO, Asset Watcher):

```bash
cd frappe-bench
bench start
```

Once running, access the application in your browser at:
👉 **[http://localhost:8000](http://localhost:8000)** (or `http://127.0.0.1:8000`)

---

## 🔑 Default Login Credentials

- **URL**: [http://localhost:8000/app](http://localhost:8000/app)
- **Username / Email**: `Administrator` (or `admin@example.com`)
- **Password**: `admin`

---

## 📂 Project Directory Architecture

Frappe applications follow a strict **Metadata-Driven MVC** architecture. Here is what every file and folder does:

```
krushi-vikas-dev/
├── pyproject.toml              # Python package metadata and dependencies
├── license.txt                 # MIT License declaration
├── README.md                   # Setup documentation & developer guide
├── .editorconfig / .eslintrc   # Code style, formatting, and linting rules
│
├── backups/                    # Seed site backups & demo database dump (.sql.gz)
│   ├── 20260816_234450-dev_localhost-database.sql.gz
│   ├── 20260816_234450-dev_localhost-site_config_backup.json
│   └── *.tar                   # Public and private uploaded files
│
└── krushi_vikas/               # Primary Python package
    ├── __init__.py
    ├── hooks.py                # Central app registry: hooks, events, routes, fixtures
    ├── modules.txt             # Registered Frappe module names (e.g., Krushi Vikas)
    ├── patches.txt             # Database migration patches history
    │
    ├── fixtures/               # Auto-synced customizations (custom fields, roles)
    │   ├── custom_field.json
    │   ├── property_setter.json
    │   └── role.json
    │
    └── krushi_vikas/           # Core module folder
        ├── doctype/            # All custom DocTypes (Database Tables & Models)
        │   ├── concept_note/
        │   │   ├── concept_note.json       # Schema definition (fields, types, permissions)
        │   │   └── concept_note.py         # Controller logic (validation, lifecycle hooks)
        │   ├── activity_outcome/
        │   ├── beneficiary/
        │   ├── improvement_suggestion/
        │   ├── input_distribution/
        │   ├── kre/
        │   ├── kre_measurement/
        │   ├── project_goal/
        │   ├── project_objective/
        │   ├── project_theme/
        │   ├── survey_template/
        │   ├── survey_question/
        │   ├── survey_response/
        │   ├── survey_answer/
        │   └── user_target/
        │
        └── workspace/          # Desk Workspaces & navigation pages
            └── krushi_vikas/
                └── krushi_vikas.json
```

### Why This Structure?
1. **`.json` Schema Definition**: In Frappe, you declare fields and data types inside `<doctype_name>.json`. Frappe reads this JSON to automatically generate and alter MariaDB SQL tables during `bench migrate` — no manual SQL `CREATE TABLE` required.
2. **`.py` Controller Logic**: `<doctype_name>.py` contains backend validation (`validate()`, `before_save()`, `on_submit()`).
3. **`.js` Client Logic**: (Optional) contains client-side Desk triggers, event listeners, and dynamic UI behavior.
4. **`hooks.py`**: Connects this app into Frappe's core lifecycle (document hooks, cron scheduler events,Desk assets, and fixture exports).

---

## 🛠️ Development Workflow

1. **Making Changes to DocTypes**:
   - Enable developer mode in `sites/frappe.local/site_config.json`: `"developer_mode": 1`.
   - Edit or add DocTypes in the Frappe Desk UI or directly in code.
2. **Syncing Database Schema**:
   - Run `bench --site frappe.local migrate` after modifying JSON definitions.
3. **Exporting Fixtures**:
   - If you add custom fields or property setters: `bench --site frappe.local export-fixtures`.
4. **Code Quality**:
   - Pre-commit hooks run automatically: `pre-commit install`.

---

## ❓ Troubleshooting & FAQ

- **Port 8000 already in use**:
  Check running processes with `fuser -k 8000/tcp` or use `bench serve --port 8001`.
- **Redis Cache / Queue Not Running**:
  Ensure Redis is started or run `bench start` which starts Redis automatically via `Procfile`.
- **Reset Admin Password**:
  Run `bench --site frappe.local set-admin-password new_password`.
