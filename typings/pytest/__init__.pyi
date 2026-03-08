from typing import Generic, Pattern, TypeVar

_E = TypeVar("_E", bound=BaseException)


class ExceptionInfo(Generic[_E]): ...


class RaisesContext(Generic[_E]):
    def __enter__(self) -> ExceptionInfo[_E]: ...
    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool | None: ...


def raises(
    expected_exception: type[_E] | tuple[type[_E], ...],
    *,
    match: str | Pattern[str] | None = ...,
) -> RaisesContext[_E]: ...
