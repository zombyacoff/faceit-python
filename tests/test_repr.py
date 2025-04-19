import pytest
from faceit._utils import _UNINITIALIZED_MARKER, representation


def test_basic_representation():
    @representation("name", "age")
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "name='John' age=30"


def test_representation_with_use_str():
    @representation("name", "age", use_str=True)
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def __str__(self):
            return f"{self.name} ({self.age})"

    person = Person("John", 30)
    assert repr(person) == "Person('John (30)')"
    assert str(person) == "John (30)"


def test_representation_with_missing_fields():
    @representation("name", "age", "email")
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age
            # `email` is not initialized

    person = Person("John", 30)
    assert repr(person) == f"Person({repr(_UNINITIALIZED_MARKER)})"


def test_representation_with_use_str_but_no_str_method():
    with pytest.raises(TypeError) as excinfo:

        @representation("name", "age", use_str=True)
        class _:
            def __init__(self, name, age):
                self.name = name
                self.age = age

    assert "must define __str__ method" in str(excinfo.value)


def test_representation_preserves_existing_str():
    @representation("name", "age")
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def __str__(self):
            return f"Person named {self.name}"

    person = Person("John", 30)
    assert repr(person) == "Person(name='John', age=30)"
    assert str(person) == "Person named John"


def test_representation_with_empty_fields():
    @representation()
    class Empty:
        pass

    empty = Empty()
    assert repr(empty) == "Empty()"
    assert str(empty) == ""
