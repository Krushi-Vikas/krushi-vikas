# Installing Krushi Vikas

## There are no database scripts, and there should not be

Frappe apps do not ship SQL. The schema lives in this repository as DocType
JSON under `krushi_vikas/krushi_vikas/doctype/`, and `bench` creates the
tables from it during `install-app` and `migrate`.

Anything that Frappe stores as *data* rather than schema — Roles, DocPerms,
Custom Fields on ERPNext's `Task` and `Project`, the workspace, the workflows
— is created by `krushi_vikas/setup_site.py` and by the fixtures in
`krushi_vikas/fixtures/`. Both now run automatically (`after_install` and
`after_migrate` in `hooks.py`).

So a clean checkout plus the commands below gives you a working, empty site.
It does **not** give you anyone's project data — that is not in the repo, and
the stray dump in `backups/` is from an unrelated frappe-only site and
contains none of this app's tables.

---

## What you need

| Component | Version used in development |
|---|---|
| Python | 3.14 (3.10+ per `pyproject.toml`) |
| Node.js | 24.x |
| MariaDB | 11.8 |
| Redis | any recent 6/7 |
| frappe-bench | 5.31 |
| Frappe framework | `develop` (17.0.0-dev) |
| ERPNext | `develop` (17.0.0-dev) — **required**, not optional |

ERPNext is a hard dependency: `Task`, `Project` and `Project Type` are its
doctypes, and most of this app's custom fields hang off them. `hooks.py`
declares `required_apps = ["erpnext"]`, so bench will refuse to install
without it rather than producing a half-broken site.

> The README describes this as a "Frappe v15" app. It is currently developed
> against `develop`/17.0.0-dev. If you must target v15, treat that as
> untested.

---

## Install

```bash
# 1. Bench, from the frappe installation docs, then:
bench init krushivikas --frappe-branch develop
cd krushivikas

# 2. Apps. ERPNext first — krushi_vikas depends on it.
bench get-app --branch develop erpnext
bench get-app https://github.com/Krushi-Vikas/krushi-vikas.git

# 3. Site. You will be asked for the MariaDB root password
#    and for a new Administrator password.
bench new-site krushivikas.local
bench --site krushivikas.local install-app erpnext
bench --site krushivikas.local install-app krushi_vikas

# 4. Assets, then run.
bench build --app krushi_vikas
bench start
```

Open <http://krushivikas.local:8000> and sign in as `Administrator`. Add
`krushivikas.local` to `/etc/hosts` pointing at `127.0.0.1` if it does not
resolve.

The dashboard is at **Krushi Vikas workspace → Dashboard**, or directly at
`/app/krushi-dashboard`.

---

## Repairing an existing site

Everything `setup_site.py` does is idempotent, so on a site that came up
incomplete:

```bash
bench --site <site> migrate        # runs setup_site.run() via after_migrate
bench build --app krushi_vikas
bench --site <site> clear-cache
```

If you would rather run the setup on its own:

```bash
bench --site <site> execute krushi_vikas.setup_site.run
```

---

## Symptoms and causes

**`bench install-app` fails while importing hooks, or the app will not load
at all.** Check `krushi_vikas/hooks.py` for `<<<<<<< HEAD` conflict markers.
They were committed to `main` and make the file invalid Python, so nothing
about the app can start. Fixed on
`feature/feature-implementation-dashboard`.

**Forms load but fields are missing — no Project Coordinator, no Project
Manager, no budget, no activities table.** Those are Custom Fields on
ERPNext's `Project`. The shipped fixture used to carry only 3 of the 18, so
a fresh install got a `Project` form that portal pages and
`api.has_project_permission` both read fields off that did not exist. Run
`bench --site <site> migrate`, then confirm:

```bash
bench --site <site> execute frappe.client.get_count \
  --kwargs '{"doctype":"Custom Field","filters":{"module":"Krushi Vikas"}}'
# expect 33
```

**Roles or permissions missing; users see everything or nothing.** The five
roles and their DocPerms come from `setup_site.py`, which previously was
never invoked automatically. `bench migrate` now creates them.

**Code changes to the dashboard do not appear in the browser.** Page JS and
CSS are bundled. Run `bench build --app krushi_vikas`, then hard-refresh.

**Workspace edits do not appear.** Frappe re-imports a workspace JSON only
when its `modified` timestamp is newer than the stored record. Bump
`modified` in `krushi_vikas/krushi_vikas/workspace/krushi_vikas/krushi_vikas.json`
before migrating.

---

## Directory structure

### The bench (what you create, not what you clone)

`bench init` generates this. Only `apps/krushi_vikas` comes from git — do
not hand-build or commit anything else here.

```
krushivikas/                        <- bench root, created by `bench init`
├── apps/
│   ├── frappe/                     <- bench get-app (framework)
│   ├── erpnext/                    <- bench get-app (required dependency)
│   └── krushi_vikas/               <- THIS REPOSITORY
├── sites/
│   ├── apps.txt                    <- generated: which apps this bench has
│   ├── common_site_config.json     <- generated: redis ports, workers
│   ├── assets/                     <- generated by `bench build`
│   └── krushivikas.local/          <- your site
│       ├── site_config.json        <- generated: db name + password
│       └── private/files/          <- uploads
├── config/                         <- generated: redis + supervisor configs
├── env/                            <- generated: python virtualenv
├── logs/                           <- generated
└── Procfile                        <- generated: what `bench start` runs
```

Everything marked *generated* is machine-specific. Copying `sites/` or
`env/` between machines does not work; run the install steps instead.

### The app (this repository)

```
krushi_vikas/
├── INSTALL.md                      <- this file
├── README.md
├── USER_JOURNEY.md                 <- role walkthroughs
├── pyproject.toml                  <- package metadata, required python
└── krushi_vikas/
    ├── hooks.py                    <- START HERE. doc_events, has_permission,
    │                                  fixtures, after_install/after_migrate,
    │                                  required_apps
    ├── api.py                      <- ~2,000 lines: whitelisted endpoints for
    │                                  the portal, plus the permission
    │                                  functions hooks.py points at
    ├── setup_site.py               <- creates roles, DocPerms, custom fields,
    │                                  workspace, workflows. Idempotent, run
    │                                  automatically on install and migrate
    ├── modules.txt                 <- declares the "Krushi Vikas" module
    ├── patches.txt
    │
    ├── fixtures/                   <- DB records shipped with the app and
    │   ├── custom_field.json          imported on migrate. 33 custom fields
    │   ├── property_setter.json       on ERPNext Task and Project.
    │   └── role.json                  property_setter.json is empty by design
    │
    ├── krushi_vikas/               <- the module itself (name repeats: app/module)
    │   ├── doctype/                <- 37 doctypes = the database schema.
    │   │   │                          Each is <name>.json (+ .py controller,
    │   │   │                          + .js desk form script). This is what
    │   │   │                          creates the tables — no SQL anywhere.
    │   │   ├── kv_project/         <- 16 parent doctypes:
    │   │   ├── activity/              Activity, Activity Outcome,
    │   │   ├── baseline_survey/       Baseline Survey, Beneficiary,
    │   │   ├── village_profile/       Concept Note, Feedback Survey,
    │   │   ├── beneficiary/           Improvement Suggestion,
    │   │   ├── kre/                   Input Distribution, KRE, KV Project,
    │   │   └── ...                    Project Goal, Project Theme, Survey
    │   │                              Response, Survey Template, User Target,
    │   │                              Village Profile
    │   │                           <- plus 21 child tables (istable: 1),
    │   │                              mostly the Baseline Survey sections
    │   │                              and KV Project Activity
    │   │
    │   ├── page/krushi_dashboard/  <- the desk dashboard
    │   │   ├── krushi_dashboard.json   Page record
    │   │   ├── krushi_dashboard.py     role scoping + admin role preview
    │   │   ├── krushi_dashboard.js     rendering (BUNDLED — needs bench build)
    │   │   └── krushi_dashboard.css
    │   │
    │   └── workspace/krushi_vikas/ <- the desk workspace: shortcuts, links and
    │                                  the tile layout. Re-imported only when
    │                                  its `modified` timestamp is newer
    │
    ├── www/                        <- the public portal, one .py + .html per
    │                                  route: projects, project_details,
    │                                  activities, activity_details, task_list,
    │                                  baseline_survey, feedback_survey,
    │                                  village_profile, structured_forms,
    │                                  reports, users
    │
    ├── public/                     <- static assets served at
    │   ├── css/                       /assets/krushi_vikas/...
    │   └── js/                        Referenced from hooks.py doctype_js and
    │                                  from the portal templates
    │
    ├── templates/pages/
    ├── config/
    └── patches/
```

### Scripts at the module root

`setup_site.py` is the one that matters; `hooks.py` runs it for you.
`api.py` is application code.

The rest — `check_boot.py`, `check_ws.py`, `check_workspace.py`,
`check_redirect.py`, `check_surveys.py`, `deep_diag.py`, `debug_sidebar.py`,
`fix_home_page.py`, `fix_workspace.py`, `fix_workspace2.py`,
`fix_installed_app.py`, `clear_defaults.py`, `enable_module.py`,
`create_ws.py`, `bypass_wizard.py`, `install_fixtures.py`, `erp_setup.py`,
`create_baseline_example.py`, `populate_baseline_sample.py` — are one-off
debugging and repair scripts committed during development. **You do not need
to run any of them to stand the app up.** Do not run them speculatively;
several mutate the workspace or site defaults.

Test scripts, run with `bench --site <site> execute <module>.run`:

| Script | Checks |
|---|---|
| `test_dashboard_scope.py` | dashboard role scoping and the admin preview (30 assertions) |
| `test_project_permissions.py` | the hierarchical ownership rules in `api.py` |
| `test_suite.py`, `test_wizard.py` | broader app flows |

### Not in the repository

- **Any project data.** A fresh install is empty by design.
- **`backups/`** contains a dump from an unrelated frappe-only site with none
  of this app's tables. It cannot restore anything and should be ignored.

---

## Verifying the install

```bash
bench --site <site> execute krushi_vikas.test_dashboard_scope.run
```

Creates two throwaway projects and five test users, then checks that each
role sees only what it should — 30 assertions. Everything should print PASS.
