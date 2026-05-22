# Test Plan

## 1. Verification Strategy

Testing will cover platform lifecycle behavior, plugin package validation, platform APIs, frontend flows, and the four reference plugins.

## 2. Test Layers

| Layer | Tool | Purpose |
| --- | --- | --- |
| Unit tests | pytest | Manifest validation, zip safety, version comparison, service logic. |
| API tests | pytest + FastAPI TestClient | Plugin admin APIs and platform APIs. |
| Integration tests | pytest | Install, enable, disable, update, uninstall flows with temporary SQLite database. |
| Frontend tests | To be selected | UI behavior after frontend stack is scaffolded. |
| Manual smoke tests | Browser | End-to-end plugin upload and usage. |

## 3. Platform Test Cases

| ID | Scenario | Expected Result |
| --- | --- | --- |
| PLAT-001 | Upload valid plugin zip | Plugin is installed and appears in plugin list. |
| PLAT-002 | Upload zip without manifest | Installation fails with clear error. |
| PLAT-003 | Upload zip with unsafe `../` path | Installation fails and no files are extracted. |
| PLAT-004 | Upload duplicate plugin as install | Installation fails and suggests update. |
| PLAT-005 | Update plugin with newer version | Active version changes and old version is not served. |
| PLAT-006 | Update plugin with older version | Update is rejected. |
| PLAT-007 | Disable plugin | Plugin disappears from sidebar and runtime calls are rejected. |
| PLAT-008 | Enable plugin | Plugin appears in sidebar and page can be opened. |
| PLAT-009 | Uninstall plugin | Metadata and package files are removed. |
| PLAT-010 | Plugin API call without permission | API returns forbidden error. |

## 4. Platform API Test Cases

| ID | Scenario | Expected Result |
| --- | --- | --- |
| API-DB-001 | SQLite read query | Returns rows and metadata. |
| API-DB-002 | SQLite invalid SQL | Returns structured error. |
| API-DB-003 | Database write without permission | Request is rejected. |
| API-SSH-001 | Build SSH command request | Request validation succeeds for valid input. |
| API-SSH-002 | Missing SSH host | Request validation fails. |
| API-SSH-003 | Batch execution partial failure | Returns per-host success and error results. |
| API-SSH-004 | Root escalation configuration | Request model supports login user and root password fields with masked logs. |

## 5. Reference Plugin Test Cases

### 5.1 JSON Formatter

| ID | Scenario | Expected Result |
| --- | --- | --- |
| JSON-001 | Input valid compact JSON | Output is formatted and readable. |
| JSON-002 | Input nested JSON | Different nesting levels use distinguishable colors. |
| JSON-003 | Input invalid JSON | Error position and message are clear. |
| JSON-004 | Input non-JSON text | Error state is obvious and no misleading output is shown. |

### 5.2 Time Converter

| ID | Scenario | Expected Result |
| --- | --- | --- |
| TIME-001 | Timestamp to datetime | Displays local time and UTC where applicable. |
| TIME-002 | Datetime to timestamp | Displays seconds and milliseconds timestamps. |
| TIME-003 | Time calculation | Adds/subtracts durations correctly. |
| TIME-004 | Invalid input | Shows clear validation error. |

### 5.3 Encoding Converter

| ID | Scenario | Expected Result |
| --- | --- | --- |
| ENC-001 | Unicode escape decode | Converts escaped text to readable text. |
| ENC-002 | Unicode escape encode | Converts text to escape sequence. |
| ENC-003 | URL/Base64 extension cases | Optional converters work if included. |
| ENC-004 | Invalid encoded input | Shows clear error. |

### 5.4 Remote Command Executor

| ID | Scenario | Expected Result |
| --- | --- | --- |
| SSH-PLUGIN-001 | Fill host/user/root/command form | Request can be submitted with valid payload. |
| SSH-PLUGIN-002 | Missing required field | UI blocks or API rejects request. |
| SSH-PLUGIN-003 | No real server available | Mocked service returns expected output in tests. |
| SSH-PLUGIN-004 | Root escalation enabled | Request includes user login and root switch config. |

## 6. Manual Validation Checklist

- Start backend successfully.
- Start frontend successfully.
- Open platform home page.
- Upload each reference plugin package.
- Confirm plugin sidebar updates after install.
- Open every plugin page.
- Disable and enable each plugin.
- Update one plugin package.
- Uninstall one plugin.
- Review operation logs.

## 7. Current Automated Verification

Current backend tests cover:

- Manifest validation.
- Plugin zip safety validation.
- Plugin lifecycle install, update, enable, disable, uninstall.
- SQLite platform API read and CRUD permission checks.
- SSH command execution models, fake executor, Paramiko executor, `su`, `sudo`, and SFTP calls with fake clients.
- Python backend plugin runtime loading.
- Reference plugin package validation, install, menu registration, and backend loading.
