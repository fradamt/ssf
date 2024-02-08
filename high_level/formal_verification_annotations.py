from typing import TypeVar, Optional, Callable, ParamSpec, NoReturn

Param = ParamSpec("Param")
RetType = TypeVar("RetType")

def Requires(expr: bool) -> None:
    pass

def Event(c:Callable[Param, RetType]) -> Callable[Param, RetType]:
    return c

def View(c:Callable[Param, RetType]) -> Callable[Param, RetType]:
    return c