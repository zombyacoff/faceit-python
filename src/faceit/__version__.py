from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__package__ or __name__)
except PackageNotFoundError:
    __version__ = "dev"
