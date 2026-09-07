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

## Verifying the install

```bash
bench --site <site> execute krushi_vikas.test_dashboard_scope.run
```

Creates two throwaway projects and five test users, then checks that each
role sees only what it should — 30 assertions. Everything should print PASS.
