try:
    from importlib import metadata
    get_version = lambda : metadata.version("binwalk")
except ImportError:
    try:
        # Running on pre-3.8 Python; use importlib-metadata package
        import importlib_metadata as metadata
        get_version = lambda: metadata.version("binwalk")
    except ImportError:
        # 3rd fallback via pkg_resources
        import pkg_resources
        get_version = lambda : pkg_resources.get_distribution("binwalk").version

__version__ = get_version()
