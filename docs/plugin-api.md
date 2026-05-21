# Plugin API Specification

## 1. API Principles

Plugins must call platform APIs through documented HTTP endpoints or a future SDK wrapper. Plugins should not directly import platform internal modules unless explicitly supported.

Each platform API call must include plugin identity and pass permission checks.

## 2. Permission Model

Supported initial permissions:

| Permission | Description |
| --- | --- |
| `database:read` | Read database metadata and execute read operations. |
| `database:write` | Execute insert, update, and delete operations. |
| `ssh:command` | Execute SSH commands. |
| `ssh:file_transfer` | Upload and download files through SSH/SFTP. |
| `ssh:batch` | Execute SSH operations on multiple hosts. |

## 3. Database API

### 3.1 Execute Query

```http
POST /api/platform/database/query
```

Request:

```json
{
  "plugin_id": "example.plugin",
  "connection": {
    "type": "sqlite",
    "database": "data/example.sqlite3"
  },
  "operation": "read",
  "sql": "select * from users limit 20",
  "params": {}
}
```

Response:

```json
{
  "success": true,
  "columns": ["id", "name"],
  "rows": [[1, "demo"]],
  "row_count": 1,
  "duration_ms": 12
}
```

### 3.2 CRUD Request Shape

```json
{
  "plugin_id": "example.plugin",
  "connection": {},
  "table": "users",
  "action": "insert",
  "data": {
    "name": "demo"
  },
  "where": {
    "id": 1
  }
}
```

The platform should internally validate table and column names. SQL parameters must be bound, not string-concatenated.

## 4. SSH API

### 4.1 Execute Command

```http
POST /api/platform/ssh/execute
```

Request:

```json
{
  "plugin_id": "remote-command",
  "host": "10.0.0.10",
  "port": 22,
  "username": "user",
  "password": "secret",
  "auth_type": "password",
  "command": "id && whoami",
  "become": {
    "enabled": true,
    "method": "su",
    "target_user": "root",
    "password": "root-secret"
  },
  "timeout_seconds": 30
}
```

Response:

```json
{
  "success": true,
  "host": "10.0.0.10",
  "stdout": "uid=0(root) gid=0(root)\nroot\n",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 320
}
```

### 4.2 Batch Execute

```http
POST /api/platform/ssh/batch-execute
```

Request:

```json
{
  "plugin_id": "remote-command",
  "hosts": [
    {
      "host": "10.0.0.10",
      "port": 22,
      "username": "user",
      "password": "secret"
    }
  ],
  "command": "hostname",
  "concurrency": 5,
  "timeout_seconds": 30
}
```

Response:

```json
{
  "success": true,
  "results": [
    {
      "host": "10.0.0.10",
      "success": true,
      "stdout": "server-1\n",
      "stderr": "",
      "exit_code": 0
    }
  ]
}
```

### 4.3 File Transfer

Upload:

```http
POST /api/platform/ssh/upload
```

Download:

```http
POST /api/platform/ssh/download
```

File transfer requests should reuse the SSH connection model and add local/remote path fields.

## 5. Error Format

All platform APIs should return consistent errors:

```json
{
  "success": false,
  "error": {
    "code": "SSH_AUTH_FAILED",
    "message": "SSH authentication failed.",
    "detail": {}
  }
}
```

Secrets must never appear in `detail`.

