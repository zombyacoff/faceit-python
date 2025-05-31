from dataclasses import dataclass
from typing import Any, Callable

import pytest

from faceit.utils import _UNINITIALIZED_MARKER, representation

DEFINE_STR_ERROR_MSG = "must define __str__ method"


@pytest.fixture(scope="session")
def dataclass_no_repr() -> Callable[..., Any]:
    return dataclass(repr=False)


def test_basic_representation(dataclass_no_repr):
    @representation("name", "age")
    @dataclass_no_repr
    class Person:
        name: str
        age: int

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "name='John' age=30"


def test_representation_with_use_str(dataclass_no_repr):
    @representation("name", "age", use_str=True)
    @dataclass_no_repr
    class Person:
        name: str
        age: int

        def __str__(self) -> str:
            return f"{self.name} ({self.age})"

    person = Person("John", 30)
    assert repr(person) == "Person('John (30)')"
    assert str(person) == "John (30)"


def test_representation_with_missing_fields(dataclass_no_repr):
    @representation("name", "age", "missing_field")
    @dataclass_no_repr
    class Person:
        name: str
        age: int

    person = Person("John", 30)
    assert repr(person) == f"Person('{_UNINITIALIZED_MARKER}')"


def test_representation_with_use_str_but_no_str_method():
    with pytest.raises(TypeError) as excinfo:
        representation("name", use_str=True)(object)
    assert DEFINE_STR_ERROR_MSG in str(excinfo.value)


def test_representation_preserves_existing_str(dataclass_no_repr):
    @representation("name", "age")
    @dataclass_no_repr
    class Person:
        name: str
        age: int

        def __str__(self) -> str:
            return f"Person named {self.name}"

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "Person named John"


def test_representation_with_empty_fields():
    with pytest.raises(TypeError) as excinfo:
        representation(object, use_str=True)()
    assert DEFINE_STR_ERROR_MSG in str(excinfo.value)

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
