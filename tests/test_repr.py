from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pytest

from faceit.utils import _UNINITIALIZED_MARKER, representation

DEFINE_STR_ERROR_MSG: Final = "must define '__str__' method"


def test_basic_representation() -> None:
    @representation("name", "age")
    @dataclass(repr=False)
    class Person:
        name: str
        age: int

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "name='John' age=30"


def test_representation_with_use_str() -> None:
    @representation("name", "age", use_str=True)
    @dataclass(repr=False)
    class Person:
        name: str
        age: int

        def __str__(self) -> str:
            return f"{self.name} ({self.age})"

    person = Person("John", 30)
    assert repr(person) == "Person('John (30)')"
    assert str(person) == "John (30)"


def test_representation_with_missing_fields() -> None:
    @representation("name", "age", "missing_field")
    @dataclass(repr=False)
    class Person:
        name: str
        age: int

    person = Person("John", 30)
    assert repr(person) == f"Person('{_UNINITIALIZED_MARKER}')"


def test_representation_with_use_str_but_no_str_method() -> None:
    with pytest.raises(TypeError, match=DEFINE_STR_ERROR_MSG):
        representation("name", use_str=True)(object)


def test_representation_preserves_existing_str() -> None:
    @representation("name", "age")
    @dataclass(repr=False)
    class Person:
        name: str
        age: int

        def __str__(self) -> str:
            return f"Person named {self.name}"

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "Person named John"


def test_representation_with_empty_fields() -> None:
    with pytest.raises(TypeError, match=DEFINE_STR_ERROR_MSG):
        representation(object, use_str=True)()

    @representation
    class Empty2:
        pass

    @representation()
    class Empty3:
        pass

    empty2 = Empty2()
    empty3 = Empty3()
    assert repr(empty2) == "Empty2()"
    assert repr(empty3) == "Empty3()"
    assert not str(empty2)
    assert not str(empty3)
