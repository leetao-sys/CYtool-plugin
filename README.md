# CYtool Plugin

CYtool Plugin 是一个基于 Python 的工具包插件框架管理平台。平台负责插件安装、注册、卸载、启用、禁用、更新、页面挂载，以及向插件提供受控的平台能力，例如 SQLite 数据访问和 SSH 远程执行。

插件以 `.zip` 包形式发布，并通过平台前端上传安装。插件源码独立放在 `plugin_sources/`，平台运行时不会直接加载该目录，而是加载用户上传后的插件包。

## 功能概览

- 插件 zip 包上传安装
- 插件元数据、菜单、页面和后端入口注册
- 插件启用、禁用、卸载、更新
- 插件私有数据目录
- 插件前端 iframe 挂载
- 插件自定义 Python 后端入口
- 平台 SQLite 数据库访问 API
- Paramiko SSH 执行器，支持普通执行、`sudo -S`、`su root`、文件上传下载和批量执行
- 示例插件：JSON 格式化、时间转换、编码转换、远程命令执行

## 技术栈

- 后端：Python、FastAPI、SQLite、Paramiko
- 前端：Vue 3、TypeScript、Vite、Element Plus
- 插件包：zip，包含 `plugin.json`、可选前端资源、可选 Python 后端代码
- 测试：pytest、ruff、Vite build

## 目录结构

```text
CYtool-plugin/
├── backend/                 # Python 后端服务
├── frontend/                # Vue 前端
├── plugin_sources/          # 示例插件源码，不由平台直接加载
├── scripts/                 # 辅助脚本
├── docs/                    # 设计、需求、API、测试文档
├── dist/plugins/            # 生成的插件 zip 发布包，默认不提交 Git
└── data/                    # 本地运行数据，默认不提交 Git
```

## 环境准备

建议使用 PowerShell，在项目根目录执行命令：

```powershell
cd D:\code\CYtool-plugin
```

安装 Python 依赖：

```powershell
python -m pip install -e .
```

安装前端依赖：

```powershell
cd D:\code\CYtool-plugin\frontend
npm.cmd install
```

## 启动项目

### 1. 启动后端

默认使用真实 Paramiko SSH 执行器：

```powershell
cd D:\code\CYtool-plugin
$env:PYTHONPATH="D:\code\CYtool-plugin\backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

后端地址：

```text
http://127.0.0.1:8000
```

如果本地没有 SSH 服务器，只想验证页面和流程，可以使用假 SSH 执行器：

```powershell
cd D:\code\CYtool-plugin
$env:PYTHONPATH="D:\code\CYtool-plugin\backend"
$env:CYTOOL_SSH_EXECUTOR="fake"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 2. 启动前端

另开一个 PowerShell：

```powershell
cd D:\code\CYtool-plugin\frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

前端地址：

```text
http://127.0.0.1:5173
```

## 打包命令

### 打包示例插件 zip

示例插件源码位于：

```text
D:\code\CYtool-plugin\plugin_sources
```

生成可上传到平台的插件 zip 包：

```powershell
cd D:\code\CYtool-plugin
python scripts\package_reference_plugins.py
```

生成结果：

```text
D:\code\CYtool-plugin\dist\plugins
```

目前会生成：

```text
encoding_converter.zip
json_formatter.zip
remote_command.zip
time_converter.zip
```

打开前端页面后，在“插件管理”里选择这些 zip 文件即可安装。

### 构建前端生产包

```powershell
cd D:\code\CYtool-plugin\frontend
npm.cmd run build
```

构建产物位于：

```text
D:\code\CYtool-plugin\frontend\dist
```

## 验证命令

运行后端测试：

```powershell
cd D:\code\CYtool-plugin
python -m pytest backend\tests
```

运行代码规范检查：

```powershell
cd D:\code\CYtool-plugin
python -m ruff check backend scripts
```

运行前端构建验证：

```powershell
cd D:\code\CYtool-plugin\frontend
npm.cmd run build
```

## 文档

- [中文综合需求、设计与开发文档](docs/product-design-development.zh-CN.md)
- [需求文档](docs/requirements.md)
- [架构设计](docs/design.md)
- [插件 API 规范](docs/plugin-api.md)
- [插件包规范](docs/plugin-package.md)
- [开发指南](docs/development.md)
- [测试计划](docs/test-plan.md)
- [路线图](docs/roadmap.md)

## 示例插件

仓库内置以下示例插件源码，用于开发和验证：

- JSON 格式化与查看
- 时间转换与时间计算
- 编码转换
- 远程服务器命令执行
