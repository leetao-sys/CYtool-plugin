# Development Guide

## 1. Development Phases

### Phase 1: Platform Skeleton

- Create backend FastAPI app.
- Create SQLite metadata models.
- Create plugin manifest schema.
- Create plugin package validator.
- Create plugin install/list/enable/disable/uninstall/update APIs.
- Create frontend layout and plugin management page.

### Phase 2: Plugin Runtime

- Serve plugin frontend assets.
- Generate sidebar menu from enabled plugins.
- Mount plugin pages.
- Enforce plugin enabled status.
- Add operation logs.

### Phase 3: Platform APIs

- Add database API service.
- Add SSH command service.
- Add SSH file transfer service.
- Add batch execution model.
- Add root escalation request model.

### Phase 4: Reference Plugins

- Build JSON formatter plugin.
- Build time converter plugin.
- Build encoding converter plugin.
- Build remote command plugin.
- Package each as zip.
- Use them as install/update/enable/disable validation fixtures.

### Phase 5: Packaging Evaluation

- Build frontend static assets.
- Serve frontend from backend.
- Evaluate PyInstaller `.exe` package size.

## 2. Code Quality Rules

- Prefer small modules with single responsibility.
- Use typed request and response schemas.
- Keep platform API errors consistent.
- Keep secrets out of logs.
- Add tests for every lifecycle branch.
- Do not make plugins depend on platform private modules.
- Keep plugin manifest schema versioned.

## 3. Backend Coding Conventions

- Use `snake_case` for Python modules, functions, and variables.
- Use Pydantic models for request and response validation.
- Keep database access inside repository/service modules.
- Raise domain-specific exceptions and convert them to HTTP errors at API boundary.
- Use dependency injection for database session and config.

## 4. Frontend Coding Conventions

- Use TypeScript for API contracts.
- Keep platform pages separate from plugin page mounting code.
- Use consistent form validation and error display.
- Avoid leaking raw exception text in user-facing UI.
- Display long command output in copyable, scrollable blocks.

## 5. Suggested Initial Commands

These commands will be finalized after scaffolding:

```bash
cd backend
python -m venv .venv
pip install -r requirements-dev.txt
pytest
```

```bash
cd frontend
npm install
npm run dev
```

## 6. Development Risks

| Risk | Mitigation |
| --- | --- |
| Arbitrary plugin code execution | Start with static frontend plugins and platform APIs. |
| SSH password leakage | Mask secrets in logs and responses. |
| Plugin asset conflicts | Use iframe isolation first. |
| Failed update breaks plugin | Use staging directory and rollback metadata. |
| `.exe` package too large | Evaluate after web version works; keep dependencies modest. |

