import asyncio
from functools import partial
from typing import (
    Any,
    Callable,
    Concatenate,
    Coroutine,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
)

import anyio


T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")


AsyncActionFunction = Callable[Concatenate[T, P], Coroutine[Any, Any, R]]
SyncActionFunction = Callable[Concatenate[T, P], R]
ActionFunction = Callable[Concatenate[T, P], R | Coroutine[Any, Any, R]]


async def run_in_threadpool(
    func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
) -> R:
    if kwargs:
        func = partial(func, **kwargs)  # type: ignore
    return await anyio.to_thread.run_sync(func, *args)


T_contra = TypeVar("T_contra", contravariant=True)
R_co = TypeVar("R_co", covariant=True)


class Action(Generic[T_contra, P, R_co]):
    def __init__(
        self,
        func: ActionFunction[T_contra, P, R_co],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self.is_async = True if asyncio.iscoroutinefunction(func) else False
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def __call__(self, block: T_contra) -> R_co:
        if self.is_async:
            self.func = cast(AsyncActionFunction[T_contra, P, R_co], self.func)
            return await self.func(block, *self.args, **self.kwargs)
        self.func = cast(SyncActionFunction[T_contra, P, R_co], self.func)
        return await run_in_threadpool(self.func, block, *self.args, **self.kwargs)
