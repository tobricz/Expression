from abc import abstractmethod
from typing import Iterable, Iterator, Sized, TypeVar, Callable, Optional, cast
import sys

from fslash.core import Option_, Some, Nothing, pipe, identity, compose
from . import seq as Seq

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TState = TypeVar("TState")


class List(Iterable[TSource], Sized):
    """Immutable list type.

    This is not the most space efficient implementation of a list. If
    that is the goal then use the builin mutable list or array types
    instead. Use this list if you need an immutable list for prepend
    operations mostly (`O(1)`).

    Example:
        >>> xs = Cons(5, Cons(4, Cons(3, Cons(2, Cons(1, Nil)))))
        >>> ys = empty.cons(1).cons(2).cons(3).cons(4).cons(5)
    """

    def match(self, *args, **kw):
        from pampy import match

        return match(self, *args, **kw)

    def pipe(self, *args):
        """Pipe list through the given functions."""
        return pipe(self, *args)

    @abstractmethod
    def append(self, other: "List[TSource]") -> "List[TSource]":
        raise NotImplementedError

    @abstractmethod
    def choose(sef, chooser: Callable[[TSource], Option_[TResult]]) -> "List[TResult]":
        raise NotImplementedError

    @abstractmethod
    def collect(self, mapping: Callable[[TSource], "List[TResult]"]) -> "List[TResult]":
        raise NotImplementedError

    @abstractmethod
    def cons(self, element: TSource) -> "List[TSource]":
        """Add element to front of List."""

        raise NotImplementedError

    @abstractmethod
    def filter(self, predicate: Callable[[TSource], bool]) -> "List[TSource]":
        raise NotImplementedError

    @abstractmethod
    def head(self) -> TSource:
        """Retrive first element in List."""

        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        """Return `True` if list is empty."""

        raise NotImplementedError

    @abstractmethod
    def map(self, mapper: Callable[[TSource], TResult]) -> "List[TResult]":
        raise NotImplementedError

    @abstractmethod
    def skip(self, count: int) -> "List[TSource]":
        """Returns the list after removing the first N elements.

        Args:
            count: The number of elements to skip.

        Returns:
            The list after removing the first N elements.
        """
        raise NotImplementedError

    @abstractmethod
    def skip_last(self, count: int) -> 'List[TSource]':
        raise NotImplementedError

    @abstractmethod
    def tail(self) -> "List[TSource]":
        """Return tail of List."""

        raise NotImplementedError

    @abstractmethod
    def take(self, count: int) -> "List[TSource]":
        """Returns the first N elements of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """
        raise NotImplementedError

    @abstractmethod
    def take_last(self, count: int) -> "List[TSource]":
        """Returns a specified number of contiguous elements from the
        end of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """
        raise NotImplementedError

    @abstractmethod
    def try_head(self) -> Option_[TSource]:
        """Returns the first element of the list, or None if the list is
        empty.
        """
        raise NotImplementedError

    def slice(
        self, start: Optional[int] = None, stop: Optional[int] = None, step: Optional[int] = None
    ) -> 'List[TSource]':
        """The slice operator.

        Slices the given list. It is basically a wrapper around the operators
        - skip
        - skip_last
        - take
        - take_last
        - filter_indexed

        The following diagram helps you remember how slices works with streams.

        Positive numbers are relative to the start of the events, while negative
        numbers are relative to the end (close) of the stream.

        .. code::

            r---e---a---c---t---i---v---e---!
            0   1   2   3   4   5   6   7   8
        -8  -7  -6  -5  -4  -3  -2  -1   0

        Examples:
            >>> result = xs.slice(1, 10)
            >>> result = xs.slice(1, -2)
            >>> result = xs.slice(1, -1, 2)

        Args:
            source: Observable to slice

        Returns:
            A sliced list.
        """
        pipeline = []

        _start: int = 0 if start is None else start
        _stop: int = sys.maxsize if stop is None else stop
        _step: int = 1 if step is None else step

        if _stop >= 0:
            pipeline.append(take(_stop))

        if _start > 0:
            pipeline.append(skip(_start))

        elif _start < 0:
            pipeline.append(take_last(-_start))

        if _stop < 0:
            pipeline.append(skip_last(-_stop))

        if _step > 1:
            pipeline.append(compose(Seq.zip(Seq.init_infinite(identity)), Seq.filter(lambda t: t[0] % _step == 0)))
        elif _step < 0:
            # Reversing events is not supported
            raise TypeError("Negative step not supported.")

        return self.pipe(*pipeline)

    @abstractmethod
    def __iter__(self) -> Iterator:
        """Return iterator for List."""

        raise NotImplementedError

    @abstractmethod
    def __add__(self, other) -> "List[TSource]":
        """Append list with other list."""

        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Return true if list equals other list."""

        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """Return length of List."""

        raise NotImplementedError


class Cons(List[TSource]):
    def __init__(self, head: TSource, tail: List[TSource]):
        self._value = (head, tail)
        self._len = 1 + len(tail)

    def append(self, other: List[TSource]) -> List[TSource]:
        head, tail = self._value
        return Cons(head, tail.append(other))

    def choose(self, chooser: Callable[[TSource], Option_[TResult]]) -> List[TResult]:
        head, tail = self._value
        filtered: List[TResult] = tail.choose(chooser)
        return cast(List[TResult], of_option(chooser(head))).append(filtered)

    def collect(self, mapping: Callable[[TSource], List[TResult]]) -> List[TResult]:
        head, tail = self._value
        return mapping(head).append(tail.collect(mapping))

    def cons(self, element: TSource) -> List[TSource]:
        """Add element to front of List."""

        return Cons(element, self)

    def filter(self, predicate: Callable[[TSource], bool]) -> List[TSource]:
        head, tail = self._value

        filtered = tail.filter(predicate)
        return Cons(head, filtered) if predicate(head) else filtered

    def head(self) -> TSource:
        """Retrive first element in List."""

        head, _ = self._value
        return head

    def is_empty(self) -> bool:
        """Return `True` if list is empty."""
        return False

    def map(self, mapper: Callable[[TSource], TResult]) -> List[TResult]:
        head, tail = self._value
        return Cons(mapper(head), tail.map(mapper))

    def skip(self, count: int) -> "List[TSource]":
        """Returns the list after removing the first N elements."""
        if count == 0:
            return self

        _, tail = self._value
        return tail.skip(count - 1)

    def skip_last(self, count: int) -> 'List[TSource]':
        """Returns the list after removing the last N elements."""
        if count == 0:
            return self

        head, tail = self._value
        queue = tail if tail is Nil else tail.skip_last(count)
        return Cons(head, queue) if len(tail) >= count else queue

    def tail(self) -> List[TSource]:
        """Return tail of List."""

        _, tail = self._value
        return tail

    def take(self, count: int) -> "List[TSource]":
        """Returns the first N elements of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """

        if not count:
            return Nil
        head, tail = self._value
        return Cons(head, tail.take(count - 1))

    def take_last(self, count: int) -> "List[TSource]":
        """Returns a specified number of contiguous elements from the
        end of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """
        if not count:
            return Nil

        head, tail = self._value
        queue = tail if tail is Nil else tail.take_last(count)
        return Cons(head, queue) if len(queue) < count else queue

    def try_head(self) -> Option_[TSource]:
        """Returns the first element of the list, or None if the list is
        empty.
        """

        head, _ = self._value
        return Some(head)

    def __add__(self, other) -> List[TSource]:
        """Append list with other list."""

        return self.append(other)

    def __eq__(self, other) -> bool:
        """Return true if list equals other list."""

        if other is Nil:
            return False

        head, tail = self._value
        return head == other.head() and tail == other.tail()

    def __iter__(self):
        head, tail = self._value
        yield head
        yield from tail

    def __len__(self) -> int:
        """Return length of List."""

        return self._len


class _Nil(List[TSource]):
    """The List Nil case class.

    Do not use. Use the singleton Nil instead.
    """

    def append(self, other: List[TSource]) -> List[TSource]:
        return other

    def choose(self, chooser: Callable[[TSource], Option_[TResult]]) -> List[TResult]:
        return Nil

    def collect(self, mapping: Callable[[TSource], List[TResult]]) -> List[TResult]:
        return Nil

    def is_empty(self) -> bool:
        """Return `True` if list is empty."""
        return True

    def cons(self, element: TSource) -> List[TSource]:
        """Add element to front of List."""

        return Cons(element, self)

    def filter(self, predicate: Callable[[TSource], bool]) -> List[TSource]:
        return Nil

    def head(self) -> TSource:
        """Retrive first element in List."""

        raise IndexError("List is empty")

    def map(self, mapping: Callable[[TSource], TResult]) -> List[TResult]:
        return Nil

    def skip(self, count: int) -> "List[TSource]":
        """Returns the list after removing the first N elements.

        Args:
            count: The number of elements to skip.
        Returns:
            The list after removing the first N elements.
        """
        if count == 0:
            return self

        raise ValueError("List is empty")

    def skip_last(self, count: int) -> 'List[TSource]':
        if count == 0:
            return self

        raise ValueError("List is empty.")

    def tail(self) -> List[TSource]:
        """Return tail of List."""

        raise IndexError("List is empty")

    def take(self, count: int) -> "List[TSource]":
        """Returns the first N elements of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """
        if not count:
            return Nil
        raise ValueError("List is empty.")

    def take_last(self, count: int) -> "List[TSource]":
        """Returns a specified number of contiguous elements from the
        end of the list.

        Args:
            count: The number of items to take.

        Returns:
            The result list.
        """
        if not count:
            return Nil
        raise ValueError("List is empty.")

    def try_head(self) -> Option_[TSource]:
        """Returns the first element of the list, or None if the list is
        empty.
        """
        return Nothing

    def __add__(self, other) -> List[TSource]:
        """Append list with other list."""

        return other

    def __eq__(self, other) -> bool:
        """Return true if list equals other list."""

        return other is Nil

    def __iter__(self):
        while False:
            yield

    def __len__(self) -> int:
        """Return length of List."""

        return 0


Nil: _Nil = _Nil()


def append(source: List[TSource]) -> Callable[[List[TSource]], List[TSource]]:
    def _append(other: List[TSource]) -> List[TSource]:
        return source.append(other)

    return _append


def choose(sef, chooser: Callable[[TSource], Option_[TResult]]) -> Callable[[List[TSource]], List[TResult]]:
    def _choose(source: List[TSource]) -> List[TResult]:
        return source.choose(chooser)

    return _choose


def collect(mapping: Callable[[TSource], List[TResult]]) -> Callable[[List[TSource]], List[TResult]]:
    def _collect(source: List[TSource]) -> List[TResult]:
        return source.collect(mapping)

    return _collect


def concat(sources: Iterable[List[TSource]]) -> List[TSource]:
    def folder(xs: List[TSource], acc: List[TSource]) -> List[TSource]:
        return xs + acc

    return Seq.fold_back(folder, sources)(Nil)


empty = Nil
"""The empty list."""


def filter(predicate: Callable[[TSource], bool]) -> Callable[[List[TSource]], List[TSource]]:
    """Returns a new collection containing only the elements of the
    collection for which the given predicate returns `True`

    Args:
        predicate: The function to test the input elements.

    Returns:
        Partially applied filter function.
    """
    def _filter(source: List[TSource]) -> List[TSource]:
        """Returns a new collection containing only the elements of the
        collection for which the given predicate returns `True`

        Args:
            source: The input list..

        Returns:
            A list containing only the elements that satisfy the predicate.
        """
        return source.filter(predicate)

    return _filter


def head(source: List[TSource]) -> TSource:
    return source.head()


def is_empty(source: List[TSource]) -> bool:
    return source.is_empty()


def map(mapper: Callable[[TSource], TResult]) -> Callable[[List[TSource]], List[TResult]]:
    def _map(source: List[TSource]) -> List[TResult]:
        return source.map(mapper)

    return _map


def of_seq(xs: Iterable[TSource]) -> List[TSource]:
    def folder(value: TSource, acc: List[TSource]) -> List[TSource]:
        return Cons(value, acc)

    return Seq.fold_back(folder, xs)(Nil)


def of_option(option: Option_[TSource]) -> List[TSource]:
    if isinstance(option, Some):
        return singleton(option.value)
    return empty


def singleton(value: TSource) -> List[TSource]:
    return Cons(value, Nil)


def skip(count: int) -> Callable[[List[TSource]], List[TResult]]:
    """Returns the list after removing the first N elements.

    Args:
        count: The number of elements to skip.
    Returns:
        The list after removing the first N elements.
    """

    def _skip(source: List[TSource]) -> List[TResult]:
        return source.skip(count)

    return _skip


def skip_last(count: int) -> Callable[[List[TSource]], List[TResult]]:
    """Returns the list after removing the last N elements.

    Args:
        count: The number of elements to skip.
    Returns:
        The list after removing the last N elements.
    """

    def _skip_last(source: List[TSource]) -> List[TResult]:
        return source.skip_last(count)

    return _skip_last


def tail(source: List[TSource]) -> List[TSource]:
    return source.tail()


def take(count: int) -> Callable[[List[TSource]], List[TSource]]:
    """Returns the first N elements of the list.

    Args:
        count: The number of items to take.

    Returns:
        The result list.
    """

    def _take(source: List[TSource]) -> List[TSource]:
        return source.take(count)

    return _take


def take_last(count: int) -> Callable[[List[TSource]], List[TSource]]:
    """Returns a specified number of contiguous elements from the end of
    the list.

    Args:
        count: The number of items to take.

    Returns:
        The result list.
    """

    def _take(source: List[TSource]) -> List[TSource]:
        return source.take_last(count)

    return _take


def try_head(self) -> Callable[[List[TSource]], Option_[TSource]]:
    """Returns the first element of the list, or None if the list is
    empty.
    """

    def _try_head(source: List[TSource]) -> Option_[TSource]:
        return source.try_head()

    return _try_head


__all__ = [
    "List",
    "Cons",
    "Nil",
    "append",
    "choose",
    "collect",
    "concat",
    "empty",
    "filter",
    "head",
    "is_empty",
    "map",
    "of_seq",
    "of_option",
    "singleton",
    "tail",
]
