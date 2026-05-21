# Requirements

## 1. Project Background

CYtool Plugin is a Python-based tool plugin framework and management platform. It allows users to import independently developed plugin zip packages through a web frontend, then install, register, enable, disable, update, uninstall, and use those plugins in the platform.

The platform is not a single fixed tool. It is a host system for many small operational tools. Each installed plugin can expose its own menu item, page, backend handlers, and platform API usage.

## 2. Target Users

- Operations engineers who need database, SSH, encoding, time, and format tools.
- Developers who build internal utility plugins.
- Administrators who manage installed plugins and their availability.

## 3. Product Scope

### 3.1 Platform Features

| Feature | Priority | Description |
| --- | --- | --- |
| Plugin upload | P0 | Upload a plugin zip package from the web UI. |
| Plugin validation | P0 | Validate manifest, package structure, plugin ID, version, permissions, and compatibility. |
| Plugin installation | P0 | Extract plugin package, persist metadata, register menu and routes. |
| Plugin list | P0 | Display installed plugins, status, version, description, and available actions. |
| Plugin enable/disable | P0 | Toggle whether a plugin appears in the plugin menu and can be invoked. |
| Plugin uninstall | P0 | Remove plugin registration and package files after safety checks. |
| Plugin update | P0 | Install a newer zip package for the same plugin ID, preserve compatible plugin data. |
| Plugin page display | P0 | Show one menu entry per enabled plugin and load the plugin page when clicked. |
| Plugin logs | P1 | Show plugin lifecycle logs and runtime errors. |
| Plugin configuration | P1 | Allow plugin-level configuration where defined by manifest. |
| Plugin permission display | P1 | Show what platform APIs each plugin requests. |

### 3.2 Platform APIs For Plugins

The platform must provide controlled APIs for plugins. Plugins should not directly access arbitrary platform internals.

| API Area | Priority | Description |
| --- | --- | --- |
| Local database API | P0 | Connect to local SQLite or supported local database files, execute CRUD operations. |
| Remote database API | P0 | Connect to remote databases using user-provided connection info, execute CRUD operations. |
| SSH command API | P0 | Connect to remote host and execute shell commands. |
| SSH file transfer API | P0 | Upload and download files through SFTP. |
| SSH batch execution API | P0 | Execute commands on multiple hosts and collect per-host results. |
| SSH user-to-root escalation | P0 | Login as normal user, then switch to root with `su` when direct root login is unavailable. |
| Secure secret handling | P0 | Avoid storing plaintext passwords where possible; mask secrets in logs and UI. |

### 3.3 Reference Plugins Required For Validation

| Plugin | Priority | Description |
| --- | --- | --- |
| JSON formatter | P0 | Convert and format JSON text. Display clear errors for invalid JSON. Render formatted nodes with level-based colors. |
| Time converter | P0 | Timestamp conversion, date-time conversion, and time calculation. |
| Encoding converter | P0 | Unicode conversion and common encoding conversions. |
| Remote command executor | P0 | Input SSH user, connect to server, switch to root, run command, and display command output. No real server verification is required initially. |

## 4. Functional Requirements

### 4.1 Plugin Installation

- User uploads a zip package in the platform UI.
- Platform validates package size, extension, manifest existence, manifest schema, plugin ID, plugin version, and compatibility.
- Platform rejects plugins with duplicate plugin ID unless the action is update.
- Platform extracts plugin into an isolated plugin directory.
- Platform persists plugin metadata into SQLite.
- Platform registers plugin menu items and backend routes.
- Platform records install logs and errors.

### 4.2 Plugin Registration

Each plugin must provide a manifest that declares:

- Plugin ID
- Name
- Version
- Description
- Author
- Platform API version compatibility
- Menu title and icon
- Frontend entry path
- Backend entry module if needed
- Requested platform API permissions

### 4.3 Plugin Uninstall

- Disabled or enabled plugins can be uninstalled.
- Platform must stop exposing plugin menus and routes before removing files.
- Platform removes plugin metadata from SQLite.
- Platform removes plugin package files.
- Platform should optionally preserve plugin data in a future backup feature.

### 4.4 Plugin Enable And Disable

- Disabled plugin is installed but hidden from the plugin menu.
- Disabled plugin backend routes should reject normal plugin use.
- Enable action restores menu and route availability.
- Platform should not delete plugin data when disabling.

### 4.5 Plugin Update

- User uploads a zip package with the same plugin ID and a newer version.
- Platform validates compatibility.
- Platform backs up existing plugin metadata before update.
- Platform replaces plugin files atomically where practical.
- On update failure, platform rolls back to the previous working version.
- Plugin data migration is reserved as an extension point.

### 4.6 Plugin Page Display

- The left plugin sidebar displays one menu item per enabled plugin.
- Clicking a menu item loads the plugin page.
- Plugin page can be implemented as bundled frontend assets or a platform-rendered page based on plugin metadata.
- Initial implementation should prefer iframe or isolated asset mounting to reduce CSS and JavaScript conflicts between plugins.

### 4.7 Database API

- Plugin page collects connection information, database type, table name, SQL, or CRUD parameters.
- Platform validates connection information.
- Platform creates database connections through a controlled service layer.
- Platform returns structured success or error responses.
- Platform must log operation metadata without logging sensitive credentials.
- Initial P0 database support should include SQLite. Remote database adapters can be added behind a common interface.

### 4.8 SSH API

- Plugin page collects host, port, username, authentication method, target command, and optional root escalation information.
- Platform supports command execution and returns stdout, stderr, exit code, start time, end time, and duration.
- Platform supports file upload and download through SFTP.
- Platform supports batch command execution for multiple hosts.
- Platform supports login as normal user and switch to root using `su`.
- Platform must avoid leaking passwords in logs, exceptions, or browser responses.

## 5. Non-Functional Requirements

### 5.1 Maintainability

- Use layered architecture.
- Keep plugin lifecycle logic separate from platform API implementations.
- Keep frontend pages modular.
- Write tests for plugin validation, lifecycle, and API contracts.

### 5.2 Extensibility

- New platform APIs should be added through service interfaces.
- New plugins should not require changes to platform core.
- Plugin manifest schema should be versioned.
- Each plugin must get a private data directory for persistent plugin-owned files.

### 5.3 Security

- Validate zip paths to prevent zip slip attacks.
- Restrict plugin package file types and entry points.
- Require explicit permissions for database and SSH APIs.
- Mask secrets in logs and UI.
- Allow plugin packages to include custom Python backend code, but load it only through a defined runtime boundary.
- Add a future option for admin approval before enabling newly installed plugins.

### 5.4 Reliability

- Plugin install/update should be transactional as much as possible.
- Failed plugin operations should return clear errors.
- Platform should keep working when one plugin fails.

### 5.5 Portability

- Development target is normal Python runtime.
- Packaging to `.exe` can be evaluated later with PyInstaller or Nuitka.
- Keep dependencies modest to reduce final package size.

## 6. Out Of Scope For First Version

- Plugin marketplace.
- Multi-user permission system.
- Online plugin auto-update.
- Real remote database support beyond interface and optional adapter skeleton.
- Production-grade plugin sandboxing. V1 defines a controlled runtime boundary but does not provide strong sandbox isolation.
- Real SSH verification against a live server.

## 7. Confirmed Decisions

- Frontend stack: Vue 3 + TypeScript + Element Plus.
- Plugin page isolation: iframe for the first version.
- SSH privilege escalation: support both `su root` and `sudo -S`.
- Plugin private storage: each plugin gets a private data directory.
- Plugin backend code: plugin zip packages may include custom Python backend code.

## 8. Open Questions

1. Should plugin Python backend code run in-process, out-of-process, or support both modes?
2. Should plugin backend code hot reload after install/update, or require platform restart?
3. Should SSH and database passwords be stored, or entered per operation?
4. Should uploaded plugin packages require a digital signature in a later version?
