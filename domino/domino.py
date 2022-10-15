import asyncio
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any, ContextManager, Iterable, Literal, ParamSpec, TypeVar, overload

from typing_extensions import Self

from .action import Action, ActionFunction
from .block import IBlock


_touched_blocks_context_var: ContextVar[set[IBlock]] = ContextVar("touched_blocks")


class TouchContext(ContextManager["TouchContext"]):

    _token: Token[set[IBlock]]
    touched_blocks: set[IBlock]

    def __enter__(self) -> Self:
        self._token = _touched_blocks_context_var.set(set())
        return self

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self.touched_blocks = _touched_blocks_context_var.get()
        _touched_blocks_context_var.reset(self._token)


def touch(*blocks: IBlock):
    _touched_blocks_context_var.get().update(blocks)


B = TypeVar("B", bound=IBlock)
P = ParamSpec("P")


class Domino:
    def __init__(self):
        self._actions: dict[
            type[IBlock],
            Action[IBlock, ..., Any],
        ] = {}

    def place(
        self,
        block_type: type[B],
        action_func: ActionFunction[B, P, Any],
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        self._actions[block_type] = Action(action_func, *args, **kwargs)

    @overload
    async def start(
        self,
        block: IBlock,
        return_effect: Literal[False] = False,
        _direct: bool = True | False,
    ) -> Any:
        ...

    @overload
    async def start(
        self,
        block: IBlock,
        return_effect: Literal[True] = True,
        _direct: bool = True | False,
    ) -> tuple[Any, asyncio.Future[list[Any]]]:
        ...

    async def start(
        self,
        block: IBlock,
        return_effect: bool = False,
        _direct: bool = True,
    ):
        block_type = type(block)
        action = self._actions.get(block_type, None)
        if action is None:
            raise RuntimeError(f"{block_type.__name__} is not placed.")
        result, touched_blocks = await asyncio.create_task(
            self._fall_down(block, action, raise_exception=_direct)
        )
        effect = asyncio.gather(
            *(self.start(block, _direct=False) for block in touched_blocks)
        )
        if return_effect:
            return result, effect
        await effect
        return result

    async def _fall_down(
        self,
        block: IBlock,
        action: Action[IBlock, ..., Any],
        raise_exception: bool = False,
    ):
        result: Any = None
        touched_blocks: list[IBlock] = []
        try:
            await self.pre_fall_down(block, action)
            with TouchContext() as catcher:
                result = await action(block)
            touched_blocks.extend(catcher.touched_blocks)
            await self.post_fall_down(block, action, result)
        except Exception as e:
            await self.exception_fall_down(block, action, e)
            if raise_exception:
                raise e
        return result, touched_blocks

    async def pre_fall_down(
        self,
        block: IBlock,
        action: Action[Any, ..., Any],
    ):
        ...

    async def post_fall_down(
        self,
        block: IBlock,
        action: Action[Any, ..., Any],
        result: IBlock | Iterable[IBlock] | None,
    ):
        ...

    async def exception_fall_down(
        self,
        block: IBlock,
        action: Action[Any, ..., Any],
        exc: Exception,
    ):
        ...
