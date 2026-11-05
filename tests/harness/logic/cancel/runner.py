"""Cancel test suite runner for multi-client request cancellation verification.

This module provides the public entry point for the cancel test suite.
It orchestrates multiple concurrent clients where one cancels mid-request
and the others complete normally.

Test flow:
- 1 client: start, wait, cancel, drain to verify silence, then recover
- N-1 clients: start, stream the full response, then wait for cancel recovery
- All clients disconnect after coordination
"""

from __future__ import annotations

import uuid
import asyncio
from dataclasses import dataclass

from tests.state import SessionContext, CancelClientResult, NormalClientResult
from config.tests.defaults import (
    CANCEL_CLIENT_COUNT_DEFAULT,
    CANCEL_POST_SECONDS_DEFAULT,
    CANCEL_DRAIN_SECONDS_DEFAULT,
    CANCEL_REQUEST_DELAY_SECONDS,
    CANCEL_RECEIVE_SECONDS_DEFAULT,
)
from tests.harness.client.prompt import select_prompt
from tests.harness.client.websocket import build_api_key_headers
from tests.harness.reporting.terminal import dim, red, bold, green, write_line, section_header

from .output import CANCEL_TEST_MESSAGE, print_cancel_client_result, print_normal_client_results
from .clients import NormalClientRequest, CancelingClientRequest, run_normal_client, run_canceling_client


@dataclass(frozen=True)
class CancelSuiteRequest:
    """Inputs for the multi-client cancel test suite.

    Attributes:
        server_url: Server URL.
        api_key: Key of the API.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        client_count: Number of client items.
        cancel_delay_seconds: Cancel delay in seconds.
        drain_timeout_seconds: Drain timeout in seconds.
        post_cancel_wait_seconds: Post cancel wait in seconds.
        receive_timeout_seconds: Receive timeout in seconds.

    """

    server_url: str
    api_key: str | None
    gender: str
    personality: str
    client_count: int = CANCEL_CLIENT_COUNT_DEFAULT
    cancel_delay_seconds: float = CANCEL_REQUEST_DELAY_SECONDS
    drain_timeout_seconds: float = CANCEL_DRAIN_SECONDS_DEFAULT
    post_cancel_wait_seconds: float = CANCEL_POST_SECONDS_DEFAULT
    receive_timeout_seconds: float = CANCEL_RECEIVE_SECONDS_DEFAULT


def _session_context(request: CancelSuiteRequest, prompt: str) -> SessionContext:
    return SessionContext(
        session_id=str(uuid.uuid4()),
        gender=request.gender,
        personality=request.personality,
        prompt=prompt,
    )


def _print_suite_start(request: CancelSuiteRequest) -> None:
    write_line(f"\n{section_header('CANCEL TEST')}")
    display_url = request.server_url.split("?", maxsplit=1)[0]
    write_line(dim(f"  server: {display_url}"))
    write_line(dim(f"  profile: {request.gender}/{request.personality}"))
    write_line(dim(f"  clients: {request.client_count} (1 cancel, {request.client_count - 1} normal)\n"))


def _create_cancel_task(
    request: CancelSuiteRequest,
    authentication_headers: dict[str, str],
    prompt: str,
    recovery_done: asyncio.Event,
) -> asyncio.Task[CancelClientResult]:
    return asyncio.create_task(
        run_canceling_client(
            CancelingClientRequest(
                server_url=request.server_url,
                authentication_headers=authentication_headers,
                context=_session_context(request, prompt),
                user_message=CANCEL_TEST_MESSAGE,
                cancel_delay_seconds=request.cancel_delay_seconds,
                drain_timeout_seconds=request.drain_timeout_seconds,
                post_cancel_wait_seconds=request.post_cancel_wait_seconds,
                receive_timeout_seconds=request.receive_timeout_seconds,
                recovery_done=recovery_done,
            ),
        ),
    )


def _create_normal_tasks(
    request: CancelSuiteRequest,
    authentication_headers: dict[str, str],
    prompt: str,
    recovery_done: asyncio.Event,
) -> list[asyncio.Task[NormalClientResult]]:
    normal_tasks: list[asyncio.Task[NormalClientResult]] = []
    for client_index in range(request.client_count - 1):
        task = asyncio.create_task(
            run_normal_client(
                NormalClientRequest(
                    server_url=request.server_url,
                    authentication_headers=authentication_headers,
                    context=_session_context(request, prompt),
                    client_id=client_index + 1,
                    user_message=CANCEL_TEST_MESSAGE,
                    receive_timeout_seconds=request.receive_timeout_seconds,
                    wait_for_recovery=recovery_done,
                ),
            ),
        )
        normal_tasks.append(task)
    return normal_tasks


def _print_suite_results(cancel_result: CancelClientResult, normal_results: list[NormalClientResult]) -> bool:
    write_line(f"\n{bold('▶ CANCEL CLIENT RESULTS')}")
    cancel_passed, cancel_failed = print_cancel_client_result(cancel_result)

    if normal_results:
        write_line(f"\n{bold('▶ NORMAL CLIENT RESULTS')}")
        normal_passed, normal_failed = print_normal_client_results(normal_results)
    else:
        normal_passed, normal_failed = 0, 0

    total_passed = cancel_passed + normal_passed
    total_failed = cancel_failed + normal_failed
    total = total_passed + total_failed

    write_line(f"\n{dim('─' * 40)}")
    if total_failed == 0:
        write_line(f"  {green('All')} {total} tests passed")
    else:
        write_line(f"  {total_passed} passed, {red(str(total_failed))} failed")

    return total_failed == 0


async def run_cancel_suite(request: CancelSuiteRequest) -> bool:
    """Run the multi-client cancel test suite.

    Args:
        request: Cancel suite connection, profile, and timing inputs.

    Returns:
        True if all tests passed, False otherwise.

    """
    _print_suite_start(request)
    prompt = select_prompt(request.gender, request.personality)
    authentication_headers = build_api_key_headers(api_key=request.api_key)
    recovery_done = asyncio.Event()

    write_line(f"{bold('▶ STARTING CLIENTS')}")
    cancel_task = _create_cancel_task(request, authentication_headers, prompt, recovery_done)
    normal_tasks = _create_normal_tasks(request, authentication_headers, prompt, recovery_done)

    await asyncio.gather(cancel_task, *normal_tasks)
    cancel_result = cancel_task.result()
    normal_results: list[NormalClientResult] = [task.result() for task in normal_tasks]
    return _print_suite_results(cancel_result, normal_results)


__all__ = ["CancelSuiteRequest", "run_cancel_suite"]
