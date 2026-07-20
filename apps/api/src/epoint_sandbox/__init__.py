from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("epoint-sandbox-api")
except PackageNotFoundError:  # a source tree with nothing installed
    __version__ = "0.0.0"

__all__ = ["__version__"]
