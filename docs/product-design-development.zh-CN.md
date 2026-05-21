# CYtool Plugin 需求、设计与开发文档

## 1. 项目定位

CYtool Plugin 是一个基于 Python 的 Web 工具包插件框架管理平台。平台本身负责插件生命周期管理、插件菜单展示、插件页面加载、平台能力 API 暴露、权限校验和基础运行环境；具体业务工具以独立插件 zip 包的形式开发、导入、安装和使用。

核心目标是让后续新增工具时尽量不修改平台核心代码。插件开发者按照平台规范打包插件，平台管理员通过前端上传 zip，即可在左侧插件栏看到对应菜单并进入插件页面使用。

## 2. 用户与使用场景

目标用户：

- 运维人员：需要 SSH、数据库、时间、编码、JSON 等日常工具。
- 内部工具开发者：按照规范开发插件并交付 zip 包。
- 平台管理员：安装、更新、禁用、卸载插件，查看运行状态。

典型流程：

1. 开发者按照插件规范开发插件并打成 zip 包。
2. 管理员在平台前端上传 zip。
3. 平台校验插件包并安装注册。
4. 左侧插件栏新增插件菜单。
5. 用户点击菜单进入插件页面。
6. 插件页面通过平台 API 使用数据库、SSH 等能力。

## 3. 功能需求

### 3.1 插件生命周期管理

平台需要支持以下基础功能：

| 功能 | 优先级 | 说明 |
| --- | --- | --- |
| 插件上传 | P0 | 前端上传插件 zip 包。 |
| 插件校验 | P0 | 校验 zip 安全性、manifest、插件 ID、版本、权限、入口文件。 |
| 插件安装 | P0 | 解压插件包，写入 SQLite 元数据，注册菜单与运行入口。 |
| 插件列表 | P0 | 展示插件名称、版本、状态、描述、权限、操作按钮。 |
| 插件启用 | P0 | 启用后插件菜单可见，运行入口可访问。 |
| 插件禁用 | P0 | 禁用后插件菜单隐藏，插件运行接口不可调用。 |
| 插件卸载 | P0 | 移除插件注册信息和插件文件。 |
| 插件更新 | P0 | 上传同 ID 新版本 zip，校验后替换当前版本。 |
| 插件日志 | P1 | 展示安装、更新、启停、运行错误等日志。 |
| 插件配置 | P1 | 支持插件声明可配置项，由平台渲染配置表单。 |

### 3.2 插件展示形式

- 平台左侧有固定插件栏。
- 每安装并启用一个插件，插件栏新增一个菜单项。
- 点击菜单后进入插件页面。
- 初版建议使用 iframe 或静态资源隔离方式加载插件页面，避免不同插件的 CSS 和 JavaScript 互相影响。
- 插件页面通过平台提供的 HTTP API 使用数据库、SSH 等能力。

### 3.3 平台 API 能力

平台需要向插件提供受控 API，而不是让插件直接访问平台内部模块。

#### 数据库 API

能力范围：

- 本地 SQLite 数据库访问。
- 远程数据库访问接口预留。
- 表信息读取。
- 增删改查。
- 原始 SQL 查询接口。
- 参数绑定，避免 SQL 注入。
- 错误结构化返回。

初版建议：

- P0 先完整支持 SQLite。
- 远程数据库先设计统一适配器接口，后续按需接入 MySQL、PostgreSQL 等。

#### SSH API

能力范围：

- SSH 执行命令。
- 文件上传。
- 文件下载。
- 多主机批量执行命令。
- 支持无法直接 root 登录的场景：先 SSH 到普通 user，再 `su root` 执行命令。
- 返回 stdout、stderr、exit code、耗时、主机维度结果。

初版建议：

- 使用 Paramiko 实现基础 SSH 和 SFTP。
- 批量执行先用线程池或 asyncio 包装，限制并发数。
- root 切换先支持 `su root`，后续可扩展 `sudo -S`。

### 3.4 内置验证插件

平台开发完成后，需要开发以下插件用于测试验证：

| 插件 | 要求 |
| --- | --- |
| JSON 格式转换插件 | 输入 JSON 字符串，格式化展示；节点按层级颜色区分；非 JSON 输入明显报错。 |
| 时间转换插件 | 时间戳转换、日期时间转换、时间加减计算。 |
| 编码转换插件 | Unicode 转换，以及可扩展的 URL/Base64 等编码转换。 |
| 远程命令插件 | 输入 SSH user，先登录普通用户，再切 root 执行命令并显示回显；当前无服务器，不做真实联通验证，使用 mock 测试。 |

## 4. 非功能需求

### 4.1 可维护性

- 后端分层清晰：API 层、服务层、插件生命周期层、平台能力层、持久化层。
- 插件管理逻辑与 SSH/数据库能力解耦。
- 插件包规范独立成文档。
- 平台 API 使用明确的数据模型和错误格式。

### 4.2 可扩展性

- 新增平台 API 不影响已有插件。
- 新增插件不修改平台核心代码。
- manifest 需要版本化，便于未来兼容升级。
- 插件权限模型可扩展。

### 4.3 安全性

- 防止 zip slip：拒绝绝对路径、`..` 路径、异常符号链接。
- 插件权限显式声明：例如 `database:read`、`ssh:command`。
- 平台 API 调用必须校验插件 ID、启用状态和权限。
- 密码、密钥等敏感字段不能写入日志。
- 初版避免自动加载任意插件 Python 代码，降低风险。

### 4.4 可靠性

- 插件安装失败不能污染已安装插件目录。
- 插件更新失败需要回滚旧版本。
- 单个插件失败不能影响平台启动。
- API 返回统一错误格式。

### 4.5 部署与打包

- 初版以 Python Web 服务方式运行。
- 后续评估 PyInstaller 或 Nuitka 打包为 `.exe`。
- 前端构建为静态文件后可由 FastAPI 一起托管。
- SQLite 和插件运行数据放在 `data/` 目录。

## 5. 技术方案

### 5.1 推荐技术栈

| 模块 | 推荐技术 | 原因 |
| --- | --- | --- |
| 后端框架 | FastAPI | Python 生态成熟，接口清晰，测试方便。 |
| 数据校验 | Pydantic | 适合 manifest、请求体、配置校验。 |
| 平台数据库 | SQLite | 满足要求，部署简单。 |
| ORM | SQLAlchemy | 便于维护元数据模型。 |
| SSH | Paramiko | 成熟稳定，支持 SSH/SFTP。 |
| 前端 | Vue 3 + TypeScript + Vite | 开发效率高，适合管理后台。 |
| UI 组件 | Element Plus | 表格、上传、表单、弹窗体验较好。 |
| 后端测试 | pytest | Python 项目标准测试工具。 |

### 5.2 总体架构

```text
浏览器
  |
  v
前端 Web UI
  |
  v
FastAPI 后端
  |
  +-- 插件管理层
  |     +-- 插件包校验
  |     +-- 安装 / 更新 / 卸载
  |     +-- 启用 / 禁用
  |     +-- 菜单注册
  |
  +-- 插件运行层
  |     +-- manifest 加载
  |     +-- 插件页面静态资源托管
  |     +-- 插件运行分发
  |     +-- 权限校验
  |
  +-- 平台 API 层
  |     +-- 数据库服务
  |     +-- SSH 服务
  |     +-- 文件传输服务
  |
  +-- 持久化层
        +-- SQLite 元数据库
        +-- 已安装插件目录
        +-- 插件私有数据目录
```

### 5.3 推荐目录结构

```text
CYtool-plugin/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── plugins/
│   │   ├── platform_api/
│   │   └── api/
│   └── tests/
├── frontend/
│   └── src/
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

## 6. 插件包规范

插件以 zip 包上传，建议结构：

```text
plugin.zip
├── plugin.json
├── frontend/
│   └── index.html
├── assets/
└── backend/
    └── plugin.py
```

初版中 `backend/plugin.py` 可选。推荐先实现“静态插件页面 + 平台 API”的模式，降低任意 Python 插件代码执行风险。

manifest 示例：

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
  "menu": {
    "title": "JSON 格式化",
    "icon": "Document",
    "order": 100
  },
  "permissions": []
}
```

远程命令插件权限示例：

```json
{
  "permissions": ["ssh:command"]
}
```

## 7. 核心数据模型

### 7.1 Plugin

| 字段 | 说明 |
| --- | --- |
| id | 插件唯一 ID。 |
| name | 插件显示名。 |
| version | 插件版本。 |
| description | 插件描述。 |
| status | installed、enabled、disabled、failed。 |
| api_version | 插件依赖的平台 API 版本。 |
| permissions | 插件申请的平台权限。 |
| install_path | 插件安装目录。 |
| data_path | 插件私有数据目录。 |
| created_at | 安装时间。 |
| updated_at | 更新时间。 |

### 7.2 PluginMenu

| 字段 | 说明 |
| --- | --- |
| plugin_id | 所属插件。 |
| title | 左侧菜单标题。 |
| icon | 图标。 |
| route | 平台路由。 |
| frontend_entry | 插件页面入口。 |
| order | 排序。 |

### 7.3 PluginOperationLog

| 字段 | 说明 |
| --- | --- |
| id | 日志 ID。 |
| plugin_id | 关联插件。 |
| operation | install、update、uninstall、enable、disable、run。 |
| status | success、failed。 |
| message | 简要信息。 |
| detail | 结构化详情，敏感信息脱敏。 |
| created_at | 创建时间。 |

## 8. 插件生命周期设计

### 8.1 安装流程

```text
上传 zip
  -> 保存到临时目录
  -> 校验 zip 安全性
  -> 读取 plugin.json
  -> 校验 manifest schema
  -> 校验插件 ID / 版本 / 权限 / 入口文件
  -> 解压到 staging 目录
  -> 写入 SQLite 元数据
  -> 移动到 installed_plugins/{plugin_id}/{version}
  -> 注册菜单和运行入口
  -> 返回安装成功
```

### 8.2 更新流程

```text
上传同 ID 新版本 zip
  -> 校验版本号高于当前版本
  -> 解压到 staging 目录
  -> 暂停旧版本运行入口
  -> 更新元数据
  -> 切换 active install_path
  -> 成功后清理旧版本或保留备份
  -> 失败则回滚旧版本
```

### 8.3 禁用流程

- 设置插件状态为 disabled。
- 插件菜单接口不再返回该插件。
- 插件运行接口返回“插件已禁用”。
- 保留插件文件和插件数据。

### 8.4 卸载流程

- 设置插件状态为 uninstalling。
- 删除菜单和运行入口。
- 删除插件安装目录。
- 删除 SQLite 元数据。
- 后续可增加“保留插件数据备份”的选项。

## 9. API 设计

### 9.1 插件管理 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/admin/plugins/upload` | 上传并安装插件。 |
| `GET` | `/api/admin/plugins` | 查询插件列表。 |
| `POST` | `/api/admin/plugins/{plugin_id}/enable` | 启用插件。 |
| `POST` | `/api/admin/plugins/{plugin_id}/disable` | 禁用插件。 |
| `POST` | `/api/admin/plugins/{plugin_id}/update` | 更新插件。 |
| `DELETE` | `/api/admin/plugins/{plugin_id}` | 卸载插件。 |
| `GET` | `/api/admin/plugins/{plugin_id}/logs` | 查询插件日志。 |

### 9.2 插件运行 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/runtime/menus` | 获取启用插件菜单。 |
| `GET` | `/plugins/{plugin_id}/index.html` | 访问插件页面。 |
| `POST` | `/api/platform/database/query` | 数据库查询。 |
| `POST` | `/api/platform/database/crud` | 数据库 CRUD。 |
| `POST` | `/api/platform/ssh/execute` | SSH 执行命令。 |
| `POST` | `/api/platform/ssh/batch-execute` | 多主机批量执行。 |
| `POST` | `/api/platform/ssh/upload` | 文件上传。 |
| `POST` | `/api/platform/ssh/download` | 文件下载。 |

### 9.3 统一错误格式

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

## 10. 开发计划

### 阶段 1：平台骨架

- 创建 FastAPI 后端。
- 创建 SQLite 元数据库。
- 创建插件 manifest schema。
- 创建插件包安全校验。
- 创建插件安装、列表、启用、禁用、卸载、更新 API。
- 创建前端基础布局和插件管理页面。

### 阶段 2：插件运行机制

- 根据启用插件生成左侧菜单。
- 托管插件静态资源。
- 点击菜单加载插件页面。
- 插件运行入口校验启用状态。
- 增加插件操作日志。

### 阶段 3：平台 API

- 实现 SQLite 数据库查询和 CRUD。
- 设计远程数据库适配器接口。
- 实现 SSH 命令执行。
- 实现 SFTP 上传下载。
- 实现多主机批量执行。
- 实现 `su root` 请求模型和执行流程。

### 阶段 4：验证插件

- 开发 JSON 格式化插件。
- 开发时间转换插件。
- 开发编码转换插件。
- 开发远程命令插件。
- 每个插件都打包为 zip，通过平台上传验证。

### 阶段 5：测试与打包

- 编写 pytest 自动化测试。
- 前端进行基础交互验证。
- 浏览器手工冒烟测试。
- 评估 `.exe` 打包体积。

## 11. 测试计划

### 11.1 平台测试

| 用例 | 预期 |
| --- | --- |
| 上传合法插件 zip | 安装成功，插件列表可见。 |
| 上传缺少 manifest 的 zip | 安装失败，提示明确。 |
| 上传包含 `../` 路径的 zip | 拒绝安装，不解压危险路径。 |
| 启用插件 | 左侧菜单出现。 |
| 禁用插件 | 左侧菜单隐藏，运行接口拒绝。 |
| 更新插件 | 版本切换成功。 |
| 卸载插件 | 元数据和安装目录被清理。 |
| 无权限调用平台 API | 返回 forbidden 错误。 |

### 11.2 插件测试

| 插件 | 关键验证 |
| --- | --- |
| JSON 格式化 | 合法 JSON 格式化；非法 JSON 明显报错；节点颜色分层。 |
| 时间转换 | 秒/毫秒时间戳转换；日期加减；非法输入提示。 |
| 编码转换 | Unicode 编码/解码；非法输入提示。 |
| 远程命令 | 表单校验；请求模型包含 user 和 root 切换配置；使用 mock SSH 验证回显。 |

## 12. 当前建议决策

我建议第一版做以下取舍：

- 前端采用 Vue 3 + TypeScript + Element Plus。
- 后端采用 FastAPI + SQLite + SQLAlchemy。
- 插件页面初版采用 iframe 隔离。
- 插件后端 Python 代码先不作为 P0 必须能力，优先提供平台 API。
- SSH 初版支持普通用户登录后 `su root`，后续再支持 `sudo -S`。
- 远程数据库先保留适配器接口，P0 完整落地 SQLite。

## 13. 待确认问题

1. 前端采用 Vue 3 + Element Plus 是否可以？
2. 插件页面初版使用 iframe 隔离是否可以？
3. SSH 切 root 初版只支持 `su root` 是否够用，是否需要同时支持 `sudo -S`？
4. 插件是否需要保存自己的私有数据目录？
5. 第一版是否允许插件 zip 包包含并执行自定义 Python 后端代码，还是先限制为“静态页面 + 平台 API”？

