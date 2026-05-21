# Architecture Design

## 1. Architecture Overview

CYtool Plugin will use a layered Python web architecture.

```text
Browser
  |
  v
Frontend SPA
  |
  v
FastAPI Backend
  |
  +-- Plugin Management Layer
  |     +-- package validation
  |     +-- install/update/uninstall
  |     +-- enable/disable
  |     +-- menu and route registry
  |
  +-- Plugin Runtime Layer
  |     +-- manifest loader
  |     +-- plugin route dispatcher
  |     +-- plugin asset serving
  |     +-- plugin permission checks
  |
  +-- Platform API Layer
  |     +-- database service
  |     +-- SSH service
  |     +-- file transfer service
  |     +-- logging service
  |
  +-- Persistence Layer
        +-- SQLite metadata database
        +-- plugin package directory
        +-- plugin data directory
```

## 2. Recommended Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Backend framework | FastAPI | Modern Python API framework, clear schemas, easy testing. |
| Data validation | Pydantic | Strong request, manifest, and config validation. |
| Database ORM | SQLAlchemy | Maintainable SQLite metadata access and future database portability. |
| Migration | Alembic | Versioned schema changes. Can be introduced once schema stabilizes. |
| SSH | AsyncSSH or Paramiko | Paramiko is mature and simple; AsyncSSH is better for async batch execution. Start with Paramiko for lower complexity. |
| Frontend | Vue 3 + TypeScript + Vite | Good UI development speed and maintainability. |
| UI library | Element Plus | Friendly admin UI with upload, tables, dialogs, forms. |
| Tests | pytest | Python standard choice, easy FastAPI testing. |
| Packaging | PyInstaller evaluation later | Can produce `.exe`; size depends on frontend assets and Python dependencies. |

## 3. Repository Structure

```text
CYtool-plugin/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── plugins/
│   │   │   ├── manifest.py
│   │   │   ├── package.py
│   │   │   ├── registry.py
│   │   │   ├── lifecycle.py
│   │   │   └── dispatcher.py
│   │   ├── platform_api/
│   │   │   ├── database.py
│   │   │   ├── ssh.py
│   │   │   └── files.py
│   │   └── api/
│   │       ├── plugin_admin.py
│   │       └── plugin_runtime.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── plugins/
│   │   └── router/
│   └── tests/
├── plugins/
│   ├── json_formatter/
│   ├── time_converter/
│   ├── encoding_converter/
│   └── remote_command/
├── data/
│   ├── cytool.sqlite3
│   ├── installed_plugins/
│   └── plugin_data/
└── docs/
```

`data/` should be ignored by Git for normal development runtime data.

## 4. Core Domain Model

### 4.1 Plugin

| Field | Description |
| --- | --- |
| id | Stable plugin ID, globally unique inside platform. |
| name | Display name. |
| version | Semantic version. |
| description | Human-readable description. |
| status | installed, enabled, disabled, failed. |
| api_version | Platform API version expected by plugin. |
| permissions | Requested platform APIs. |
| install_path | Extracted package path. |
| data_path | Plugin private data path. |
| created_at | Install time. |
| updated_at | Update time. |

### 4.2 PluginMenu

| Field | Description |
| --- | --- |
| plugin_id | Owner plugin. |
| title | Sidebar menu title. |
| icon | Optional icon name. |
| route | Platform route path. |
| frontend_entry | HTML or asset entry path. |
| order | Sidebar order. |

### 4.3 PluginOperationLog

| Field | Description |
| --- | --- |
| id | Log ID. |
| plugin_id | Related plugin if any. |
| operation | install, update, uninstall, enable, disable, run. |
| status | success or failed. |
| message | Human-readable message. |
| detail | Structured JSON detail, secrets masked. |
| created_at | Log time. |

## 5. Plugin Lifecycle Design

### 5.1 Install Flow

```text
Upload zip
  -> save to temporary file
  -> validate zip safety
  -> read manifest
  -> validate manifest schema
  -> validate plugin ID/version/compatibility
  -> validate declared files exist
  -> extract to staging directory
  -> optionally import backend entry metadata
  -> insert metadata into SQLite transaction
  -> move staging directory to installed_plugins/{plugin_id}/{version}
  -> register menus and routes
  -> return success
```

### 5.2 Update Flow

```text
Upload zip
  -> validate same plugin_id
  -> validate newer version
  -> extract to staging directory
  -> disable old runtime route
  -> update metadata in transaction
  -> switch active install path
  -> if success, archive or remove old package
  -> if failed, rollback metadata and old install path
```

### 5.3 Disable Flow

- Set plugin status to disabled.
- Remove plugin from sidebar API result.
- Runtime dispatcher rejects plugin calls with a clear disabled error.
- Keep plugin files and data.

### 5.4 Uninstall Flow

- Mark plugin as uninstalling.
- Remove menu and route registration.
- Delete installed package directory.
- Delete metadata.
- Keep optional plugin data backup in future version.

## 6. Plugin Runtime Design

The first version should avoid unrestricted automatic execution of arbitrary plugin code at platform startup.

Recommended first-stage runtime:

- Plugin frontend is static assets loaded by the platform.
- Plugin backend capabilities are invoked through platform-defined API endpoints.
- Reference plugins use platform APIs directly through the web API instead of arbitrary backend code.

V1 custom Python runtime:

- Allow plugin-defined backend route modules.
- Load routes only after manifest validation and permission checks.
- Provide each plugin with a private data directory.
- Expose platform APIs through a controlled context object instead of private imports.
- Support a future subprocess isolation mode for untrusted plugins.

## 7. Frontend Design

### 7.1 Layout

- Left sidebar:
  - Dashboard
  - Plugin management
  - Installed plugin menu items
- Main area:
  - Plugin page or admin page
- Top area:
  - Current page title
  - Status and notification area

### 7.2 Plugin Management Page

Required controls:

- Upload plugin zip
- Plugin list table
- Enable/disable switch
- Update button
- Uninstall button
- View manifest
- View logs

### 7.3 Plugin Page Mounting

Initial recommendation:

- Use iframe to mount plugin static page for CSS/JS isolation.
- Provide a JS bridge or REST API access token for plugin page to call platform APIs.
- Keep host UI sidebar outside iframe.

## 8. Platform API Design

Platform APIs must enforce:

- Plugin identity
- Plugin enabled status
- Declared permission
- Request validation
- Secret masking
- Operation logging

More details are in `docs/plugin-api.md`.

## 9. Security Design

### 9.1 Zip Package Safety

- Reject absolute paths.
- Reject paths containing `..`.
- Reject symlinks in zip where practical.
- Limit maximum package size.
- Limit extracted file count.

### 9.2 Secret Safety

- Never store SSH passwords in plugin manifest.
- Mask passwords in request logs.
- Store connection profiles only when user explicitly asks.
- If stored, use OS credential storage or encrypted storage in a later version.

### 9.3 Plugin Permission Safety

Plugins must declare permissions:

- `database:read`
- `database:write`
- `ssh:command`
- `ssh:file_transfer`
- `ssh:batch`

The platform rejects API calls not declared in manifest.

## 10. Packaging To `.exe`

Packaging should be evaluated after the web version works.

Recommended approach:

- Build frontend into static assets.
- Let FastAPI serve static frontend assets.
- Package backend with PyInstaller.
- Store runtime data beside executable under `data/`.

Risk:

- Python packaging with SSH, ORM, and frontend assets can increase package size.
- `.exe` is useful for distribution, but should not drive the first architecture.

## 11. Design Decisions

| Decision | Initial Choice | Reason |
| --- | --- | --- |
| Backend | FastAPI | Clear API and tests. |
| Database | SQLite | Matches requirement and simple deployment. |
| Frontend | Vue 3 + TypeScript | Maintainable SPA. |
| Plugin page isolation | iframe first | Avoid style/script conflicts. |
| Plugin backend code | Allowed in V1 through controlled runtime boundary | Required for extensible plugin development. |
| SSH library | Paramiko first | Stable and widely used. |
| SSH escalation | `su root` and `sudo -S` | Required host environments differ. |

## 12. Open Questions

1. Should plugin Python backend code run in-process, out-of-process, or support both modes?
2. Should users be able to save SSH and database connection profiles?
3. Should saved secrets use OS credential storage, an encrypted local vault, or no persistence in V1?
