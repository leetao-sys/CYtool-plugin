from __future__ import annotations

from app.platform_api.database import CrudRequest, DatabaseConnection, DatabaseService, QueryRequest
from app.platform_api.errors import PlatformApiError
from app.platform_api.ssh import (
    BecomeConfig,
    SshBatchCommandRequest,
    SshCommandRequest,
    SshFileTransferRequest,
    SshHost,
    SshService,
)


def create_platform_router(database: DatabaseService, ssh: SshService):
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    router = APIRouter(prefix="/platform", tags=["platform-api"])

    class ConnectionModel(BaseModel):
        type: str = "sqlite"
        database: str

    class QueryModel(BaseModel):
        plugin_id: str
        connection: ConnectionModel
        operation: str = "read"
        sql: str
        params: dict[str, object] | None = None

    class CrudModel(BaseModel):
        plugin_id: str
        connection: ConnectionModel
        table: str
        action: str
        data: dict[str, object] | None = None
        where: dict[str, object] | None = None
        limit: int = Field(default=100, ge=1, le=1000)

    class BecomeModel(BaseModel):
        enabled: bool = False
        method: str = "su"
        target_user: str = "root"
        password: str | None = None

    class SshHostModel(BaseModel):
        host: str
        port: int = 22
        username: str
        password: str | None = None
        private_key: str | None = None
        auth_type: str = "password"
        become: BecomeModel | None = None

    class SshCommandModel(BaseModel):
        plugin_id: str
        host: SshHostModel
        command: str
        timeout_seconds: int = Field(default=30, ge=1, le=600)

    class SshBatchCommandModel(BaseModel):
        plugin_id: str
        hosts: list[SshHostModel]
        command: str
        concurrency: int = Field(default=5, ge=1, le=50)
        timeout_seconds: int = Field(default=30, ge=1, le=600)

    class SshFileTransferModel(BaseModel):
        plugin_id: str
        host: SshHostModel
        local_path: str
        remote_path: str
        timeout_seconds: int = Field(default=30, ge=1, le=600)

    @router.post("/database/query")
    def query(request: QueryModel) -> dict[str, object]:
        try:
            return database.execute_query(
                QueryRequest(
                    plugin_id=request.plugin_id,
                    connection=DatabaseConnection(
                        type=request.connection.type,  # type: ignore[arg-type]
                        database=request.connection.database,
                    ),
                    operation=request.operation,  # type: ignore[arg-type]
                    sql=request.sql,
                    params=request.params,
                )
            )
        except PlatformApiError as exc:
            raise _http_error(exc) from exc

    @router.post("/database/crud")
    def crud(request: CrudModel) -> dict[str, object]:
        try:
            return database.execute_crud(
                CrudRequest(
                    plugin_id=request.plugin_id,
                    connection=DatabaseConnection(
                        type=request.connection.type,  # type: ignore[arg-type]
                        database=request.connection.database,
                    ),
                    table=request.table,
                    action=request.action,  # type: ignore[arg-type]
                    data=request.data,
                    where=request.where,
                    limit=request.limit,
                )
            )
        except PlatformApiError as exc:
            raise _http_error(exc) from exc

    @router.post("/ssh/execute")
    def ssh_execute(request: SshCommandModel) -> dict[str, object]:
        try:
            return ssh.execute(
                SshCommandRequest(
                    plugin_id=request.plugin_id,
                    host=_ssh_host(request.host),
                    command=request.command,
                    timeout_seconds=request.timeout_seconds,
                )
            )
        except (PlatformApiError, ValueError) as exc:
            raise _http_error(exc) from exc

    @router.post("/ssh/batch-execute")
    def ssh_batch_execute(request: SshBatchCommandModel) -> dict[str, object]:
        try:
            return ssh.batch_execute(
                SshBatchCommandRequest(
                    plugin_id=request.plugin_id,
                    hosts=tuple(_ssh_host(host) for host in request.hosts),
                    command=request.command,
                    concurrency=request.concurrency,
                    timeout_seconds=request.timeout_seconds,
                )
            )
        except (PlatformApiError, ValueError) as exc:
            raise _http_error(exc) from exc

    @router.post("/ssh/upload")
    def ssh_upload(request: SshFileTransferModel) -> dict[str, object]:
        try:
            return ssh.upload(
                SshFileTransferRequest(
                    plugin_id=request.plugin_id,
                    host=_ssh_host(request.host),
                    local_path=request.local_path,
                    remote_path=request.remote_path,
                    timeout_seconds=request.timeout_seconds,
                )
            )
        except (PlatformApiError, ValueError) as exc:
            raise _http_error(exc) from exc

    @router.post("/ssh/download")
    def ssh_download(request: SshFileTransferModel) -> dict[str, object]:
        try:
            return ssh.download(
                SshFileTransferRequest(
                    plugin_id=request.plugin_id,
                    host=_ssh_host(request.host),
                    local_path=request.local_path,
                    remote_path=request.remote_path,
                    timeout_seconds=request.timeout_seconds,
                )
            )
        except (PlatformApiError, ValueError) as exc:
            raise _http_error(exc) from exc

    def _http_error(error: Exception):
        status_code = 400
        code = getattr(error, "code", "BAD_REQUEST")
        message = getattr(error, "message", str(error))
        detail = getattr(error, "detail", {})
        return HTTPException(
            status_code=status_code,
            detail={
                "success": False,
                "error": {"code": code, "message": message, "detail": detail},
            },
        )

    def _ssh_host(model: SshHostModel) -> SshHost:
        become = None
        if model.become:
            become = BecomeConfig(
                enabled=model.become.enabled,
                method=model.become.method,  # type: ignore[arg-type]
                target_user=model.become.target_user,
                password=model.become.password,
            )
        return SshHost(
            host=model.host,
            port=model.port,
            username=model.username,
            password=model.password,
            private_key=model.private_key,
            auth_type=model.auth_type,  # type: ignore[arg-type]
            become=become,
        )

    return router
