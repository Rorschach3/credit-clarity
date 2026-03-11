"""
Small async helpers.

Several tests patch async-ish services (db/job processors) with plain MagicMocks
returning dicts. `maybe_await` lets production code remain async while keeping
tests simple.
"""

from __future__ import annotations

import inspect
from typing import Any, TypeVar

T = TypeVar("T")


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value

