from __future__ import annotations

import asyncio
import socket

from uvicorn._types import WWWScope


class ClientDisconnected(OSError): ...


def get_remote_addr(transport: asyncio.Transport) -> tuple[str, int] | None:
    socket_info: socket.socket | None = transport.get_extra_info("socket")
    if socket_info is not None:
        try:
            info = socket_info.getpeername()
            return (str(info[0]), int(info[1])) if isinstance(info, tuple) else None
        except OSError:  # pragma: no cover
            # This case appears to inconsistently occur with uvloop
            # bound to a unix domain socket.
            return None

    info = transport.get_extra_info("peername")
    if info is not None and isinstance(info, list | tuple) and len(info) == 2:
        return (str(info[0]), int(info[1]))
    return None


def get_local_addr(transport: asyncio.Transport) -> tuple[str, int | None] | None:
    socket_info: socket.socket | None = transport.get_extra_info("socket")
    if socket_info is not None:
        info = socket_info.getsockname()
        if isinstance(info, tuple):
            return (str(info[0]), int(info[1]))
        if isinstance(info, str):
            return (info, None)
        return None
    info = transport.get_extra_info("sockname")
    if info is not None and isinstance(info, list | tuple) and len(info) == 2:
        return (str(info[0]), int(info[1]))
    if isinstance(info, str):
        return (info, None)
    return None


def is_ssl(transport: asyncio.Transport) -> bool:
    return bool(transport.get_extra_info("sslcontext"))


def get_client_addr(scope: WWWScope) -> str:
    client = scope.get("client")
    if not client:
        return ""
    host, port = client[0], client[1] if len(client) > 1 else None
    host_str = str(host)
    if ":" in host_str and not host_str.startswith("["):
        host_str = f"[{host_str}]"
    if port is None:
        return host_str
    return f"{host_str}:{int(port)}"


def get_path_with_query_string(scope: WWWScope) -> str:
    raw_path = scope.get("raw_path")
    if raw_path is None:
        path = scope.get("path") or "/"
        path_with_query_string = path if isinstance(path, str) else bytes(path).decode("latin1")
    else:
        path_with_query_string = bytes(raw_path).decode("latin1")
    query_string = scope.get("query_string") or b""
    if query_string:
        path_with_query_string = "{}?{}".format(path_with_query_string, bytes(query_string).decode("ascii"))
    return path_with_query_string.replace('"', "%22")
