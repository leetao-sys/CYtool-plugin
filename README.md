# CYtool Plugin

CYtool Plugin is a Python-based web platform for managing tool plugins.

The platform provides plugin lifecycle management, plugin UI mounting, shared platform APIs, and reference plugins for validation.

## Core Goals

- Install plugins from uploaded zip packages.
- Register plugin metadata, menus, pages, and backend routes.
- Uninstall plugins safely.
- Enable, disable, and update plugins.
- Provide shared APIs for plugins, including database access and SSH operations.
- Use SQLite for platform metadata.
- Provide a friendly web UI.

## Planned Technology Stack

- Backend: Python, FastAPI
- Frontend: Web UI, Vue 3 + TypeScript + Vite
- Database: SQLite
- Plugin package: zip archive with a manifest, backend module, and optional frontend assets
- Testing: pytest for backend, frontend test tooling after scaffolding

## Backend Development

```bash
$env:PYTHONPATH="D:\code\CYtool-plugin\backend"
python -m unittest discover -s backend\tests
uvicorn app.main:app --app-dir backend --reload
```

By default the platform uses the real Paramiko SSH executor. For local UI testing without real servers:

```bash
$env:CYTOOL_SSH_EXECUTOR="fake"
uvicorn app.main:app --app-dir backend --reload
```

## Reference Plugin Packages

Reference plugin sources live under `plugin_sources/`. They are not loaded directly by
the platform. Build uploadable zip packages with:

```bash
python scripts/package_reference_plugins.py
```

Generated packages are written to `dist/plugins/`; upload these `.zip` packages from
the web UI.

## Documentation

- [中文综合需求、设计与开发文档](docs/product-design-development.zh-CN.md)
- [Requirements](docs/requirements.md)
- [Architecture Design](docs/design.md)
- [Plugin API Specification](docs/plugin-api.md)
- [Plugin Package Specification](docs/plugin-package.md)
- [Development Guide](docs/development.md)
- [Test Plan](docs/test-plan.md)
- [Roadmap](docs/roadmap.md)

## Initial Reference Plugins

The repository keeps these reference plugin sources for development and verification:

- JSON formatter and viewer
- Time converter and calculator
- Encoding converter
- Remote server command executor
