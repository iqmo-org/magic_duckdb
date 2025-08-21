from magic_duckdb._version import __version__

# This must be modified before magic is initialized, before load_ipython_extension
MAGIC_NAME = "dql"

# Disable autocompletion initialization by setting this to False before loading extension
ENABLE_AUTOCOMPLETE = True


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    if ip is None:  # pragma: no cover
        raise ValueError("No ipython found")

    if ENABLE_AUTOCOMPLETE:
        from .autocomplete.common import init_completers

        init_completers(ip)

    from .magic import DuckDbMagic  # type: ignore

    ip.register_magics(DuckDbMagic)


__all__ = [
    "__version__",
]
