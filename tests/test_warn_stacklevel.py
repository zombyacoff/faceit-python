from pathlib import Path
from types import FrameType
from unittest.mock import MagicMock, patch

import pytest

from faceit.utils import _get_ignored_paths, warn_stacklevel


@pytest.fixture(autouse=True)
def clear_lru_cache() -> None:
    _get_ignored_paths.cache_clear()


class TestGetIgnoredPaths:
    def test_get_ignored_paths_init_py(self) -> None:
        mock_mod = MagicMock()
        path_str = Path("libs") / "package" / "__init__.py"
        mock_mod.__file__ = str(path_str.resolve())

        with (
            patch.dict("sys.modules", {"test_pkg": mock_mod}),
            patch("faceit.utils._IGNORED_MODULES", {"test_pkg"}),
        ):
            prefixes, _ = _get_ignored_paths()

            expected_prefix = Path(mock_mod.__file__).resolve().parent

            assert expected_prefix in prefixes

    def test_get_ignored_paths_single_file(self) -> None:
        mock_mod = MagicMock()
        fake_path = Path("external").resolve() / "mod.py"
        mock_mod.__file__ = str(fake_path)

        with (
            patch.dict("sys.modules", {"external_mod": mock_mod}),
            patch("faceit.utils._IGNORED_MODULES", {"external_mod"}),
        ):
            _, files = _get_ignored_paths()

            assert fake_path in files


class TestWarnStacklevel:
    def test_warn_stacklevel_finds_external_frame(self) -> None:
        ignored_path = Path("/faceit/internal.py").resolve()
        external_path = Path("/user_code/app.py").resolve()

        frame_ext = MagicMock(spec=FrameType)
        frame_ext.f_code.co_filename = str(external_path)
        frame_ext.f_back = None

        frame_int = MagicMock(spec=FrameType)
        frame_int.f_code.co_filename = str(ignored_path)
        frame_int.f_back = frame_ext

        with (
            patch("faceit.utils._get_ignored_paths") as mock_paths,
            patch("sys._getframe", return_value=frame_int),
        ):
            mock_paths.return_value = ((), frozenset([ignored_path]))
            assert warn_stacklevel() == 2

    def test_warn_stacklevel_fallback(self) -> None:
        with patch("sys._getframe", side_effect=ValueError):
            assert warn_stacklevel() == 1

    def test_warn_stacklevel_skips_internal_python_calls(self) -> None:
        internal_frame = MagicMock(spec=FrameType)
        internal_frame.f_code.co_filename = "<string>"
        internal_frame.f_back = None

        with patch("sys._getframe", return_value=internal_frame):
            assert warn_stacklevel() == 1


def test_integration_stack_navigation() -> None:
    def wrapper() -> int:
        return warn_stacklevel()

    current_file = Path(__file__).resolve()
    with patch(
        "faceit.utils._get_ignored_paths", return_value=((), frozenset([current_file]))
    ):
        assert wrapper() > 1
