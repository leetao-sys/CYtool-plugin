# Plugin Package Specification

## 1. Package Format

Plugins are uploaded as `.zip` files.

Required package layout:

```text
plugin.zip
├── plugin.json
├── frontend/
│   └── index.html
├── assets/
└── backend/
    └── plugin.py
```

For version 1, `backend/plugin.py` is optional but supported. Plugins may include custom Python backend code when they need server-side behavior beyond static frontend assets and platform APIs.

## 2. Manifest

`plugin.json` example:

```json
{
  "id": "json-formatter",
  "name": "JSON Formatter",
  "version": "1.0.0",
  "description": "Format and validate JSON text.",
  "author": "CYtool",
  "api_version": "1.0",
  "frontend": {
    "entry": "frontend/index.html"
  },
  "backend": {
    "entry": "backend/plugin.py",
    "factory": "create_plugin"
  },
  "menu": {
    "title": "JSON Format",
    "icon": "Document",
    "order": 100
  },
  "permissions": []
}
```

Remote command plugin example permissions:

```json
{
  "permissions": ["ssh:command"]
}
```

## 3. Manifest Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Stable unique ID. Lowercase letters, numbers, hyphen, and dot recommended. |
| `name` | Yes | Human-readable plugin name. |
| `version` | Yes | Semantic version, such as `1.0.0`. |
| `description` | Yes | Plugin description. |
| `author` | No | Plugin author. |
| `api_version` | Yes | Required platform API version. |
| `frontend.entry` | Yes | HTML entry file inside zip. |
| `backend.entry` | No | Python backend entry file inside zip. |
| `backend.factory` | No | Factory function name used to create plugin backend routes or handlers. |
| `menu.title` | Yes | Sidebar title. |
| `menu.icon` | No | UI icon name. |
| `menu.order` | No | Sort order. |
| `permissions` | Yes | Platform API permissions requested by plugin. |

## 4. Validation Rules

- Zip must contain `plugin.json`.
- Manifest must be valid JSON.
- Plugin ID must match allowed pattern.
- Version must be valid semantic version.
- `frontend.entry` must exist.
- If declared, `backend.entry` must exist and must be a Python file.
- Declared permissions must be known by the platform.
- Zip paths must be relative and must not contain `..`.
- Package size and extracted file count must be below configured limits.

## 5. Runtime Paths

Recommended runtime storage:

```text
data/
├── installed_plugins/
│   └── json-formatter/
│       └── 1.0.0/
└── plugin_data/
    └── json-formatter/
```

Plugin package files and plugin private data should be stored separately.
