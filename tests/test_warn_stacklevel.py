import os
from unittest.mock import MagicMock, patch
from types import FrameType

import pytest


@pytest.fixture(autouse=True)
def clear_lru_cache():
    from faceit.utils import _get_ignored_paths

    _get_ignored_paths.cache_clear()


class TestGetIgnoredPaths:
    def test_get_ignored_paths_init_py(self):
        mock_mod = MagicMock()
        path_str = os.path.join("libs", "package", "__init__.py")
        mock_mod.__file__ = os.path.abspath(path_str)

        with patch.dict("sys.modules", {"test_pkg": mock_mod}), patch(
            "faceit.utils._IGNORED_MODULES", {"test_pkg"}
        ):
            from faceit.utils import _get_ignored_paths

            prefixes, _ = _get_ignored_paths()

            expected_prefix = os.path.normcase(
                os.path.dirname(mock_mod.__file__) + os.sep
            )

            assert expected_prefix in prefixes

    def test_get_ignored_paths_single_file(self):
        mock_mod = MagicMock()
        fake_path = os.path.normcase(
            os.path.abspath(os.path.join("external", "mod.py"))
        )
        mock_mod.__file__ = fake_path

        with patch.dict("sys.modules", {"external_mod": mock_mod}), patch(
            "faceit.utils._IGNORED_MODULES", {"external_mod"}
        ):
            from faceit.utils import _get_ignored_paths

            _, files = _get_ignored_paths()

            assert fake_path in files


class TestWarnStacklevel:
    def test_warn_stacklevel_finds_external_frame(self):
        ignored_path = os.path.normcase(os.path.abspath("/faceit/internal.py"))
        external_path = os.path.normcase(os.path.abspath("/user_code/app.py"))

        frame_ext = MagicMock(spec=FrameType)
        frame_ext.f_code.co_filename = external_path
        frame_ext.f_back = None

        frame_int = MagicMock(spec=FrameType)
        frame_int.f_code.co_filename = ignored_path
        frame_int.f_back = frame_ext

        with patch("faceit.utils._get_ignored_paths") as mock_paths, patch(
            "sys._getframe", return_value=frame_int
        ):
            mock_paths.return_value = ((), frozenset([ignored_path]))

            from faceit.utils import warn_stacklevel

            assert warn_stacklevel() == 2

    def test_warn_stacklevel_fallback(self):
        with patch("sys._getframe", side_effect=ValueError):
            from faceit.utils import warn_stacklevel

            assert warn_stacklevel() == 1

    def test_warn_stacklevel_skips_internal_python_calls(self):
        internal_frame = MagicMock(spec=FrameType)
        internal_frame.f_code.co_filename = "<string>"
        internal_frame.f_back = None

        with patch("sys._getframe", return_value=internal_frame):
            from faceit.utils import warn_stacklevel

            assert warn_stacklevel() == 1


def test_integration_stack_navigation():
    from faceit.utils import warn_stacklevel

    def wrapper():
        return warn_stacklevel()

    current_file = os.path.normcase(os.path.realpath(__file__))
    with patch(
        "faceit.utils._get_ignored_paths", return_value=((), frozenset([current_file]))
    ):
        assert wrapper() > 1
