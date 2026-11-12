import httpx2
import pytest

from tests.middleware.test_logging import caplog_for_logger
from uvicorn._types import ASGIReceiveCallable, ASGISendCallable, Scope
from uvicorn.logging import TRACE_LOG_LEVEL
from uvicorn.middleware.message_logger import MessageLoggerMiddleware


@pytest.mark.anyio
async def test_message_logger(caplog: pytest.LogCaptureFixture) -> None:
    async def app(scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    with caplog_for_logger(caplog, "uvicorn.asgi"):
        caplog.set_level(TRACE_LOG_LEVEL, logger="uvicorn.asgi")
        caplog.set_level(TRACE_LOG_LEVEL)

        transport = httpx2.ASGITransport(MessageLoggerMiddleware(app))  # type: ignore
        async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/")
        assert response.status_code == 200
        messages = [record.msg % record.args for record in caplog.records]
        assert sum(["ASGI [1] Started" in message for message in messages]) == 1
        assert sum(["ASGI [1] Send" in message for message in messages]) == 2
        assert sum(["ASGI [1] Receive" in message for message in messages]) == 1
        assert sum(["ASGI [1] Completed" in message for message in messages]) == 1
        assert sum(["ASGI [1] Raised exception" in message for message in messages]) == 0


@pytest.mark.anyio
async def test_message_logger_exc(caplog: pytest.LogCaptureFixture) -> None:
    async def app(scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        raise RuntimeError()

    with caplog_for_logger(caplog, "uvicorn.asgi"):
        caplog.set_level(TRACE_LOG_LEVEL, logger="uvicorn.asgi")
        caplog.set_level(TRACE_LOG_LEVEL)
        transport = httpx2.ASGITransport(MessageLoggerMiddleware(app))  # type: ignore
        async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
            with pytest.raises(RuntimeError):
                await client.get("/")
        messages = [record.msg % record.args for record in caplog.records]
        assert sum(["ASGI [1] Started" in message for message in messages]) == 1
        assert sum(["ASGI [1] Send" in message for message in messages]) == 0
        assert sum(["ASGI [1] Receive" in message for message in messages]) == 0
        assert sum(["ASGI [1] Completed" in message for message in messages]) == 0
        assert sum(["ASGI [1] Raised exception" in message for message in messages]) == 1


@pytest.mark.anyio
async def test_message_logger_unix_socket_client_and_nonsized_placeholder(caplog: pytest.LogCaptureFixture) -> None:
    from uvicorn.middleware.message_logger import message_with_placeholders

    async def app(scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})

    with caplog_for_logger(caplog, "uvicorn.asgi"):
        caplog.set_level(TRACE_LOG_LEVEL, logger="uvicorn.asgi")
        caplog.set_level(TRACE_LOG_LEVEL)
        middleware = MessageLoggerMiddleware(app)  # type: ignore[arg-type]

        async def receive() -> dict[str, object]:
            return {"type": "http.request", "body": b""}

        async def send(message: dict[str, object]) -> None:
            return None

        # UNIX domain sockets commonly pass (socket_path, None) or 1-tuples as client
        await middleware({"type": "http", "client": ("/tmp/app.sock", None)}, receive, send)  # type: ignore[arg-type]
        await middleware({"type": "http", "client": ("127.0.0.1",)}, receive, send)  # type: ignore[arg-type]

        messages = [record.msg % record.args for record in caplog.records]
        assert any("/tmp/app.sock - ASGI [1] Started" in m for m in messages)
        assert any("127.0.0.1 - ASGI [2] Started" in m for m in messages)

    assert message_with_placeholders({"type": "http.request", "body": 123}) == {"type": "http.request", "body": 123}
    assert message_with_placeholders({"type": "http.request", "body": b"abc"}) == {
        "type": "http.request",
        "body": "<3 bytes>",
    }
