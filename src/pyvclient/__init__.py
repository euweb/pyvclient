# -*- coding: utf-8 -*-
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        # Change here if project is renamed and does not equal the package name
        __version__ = version(__name__)
    except PackageNotFoundError:
        __version__ = 'unknown'
except ImportError:
    # Python < 3.8 fallback
    try:
        from pkg_resources import get_distribution, DistributionNotFound
        try:
            __version__ = get_distribution(__name__).version
        except DistributionNotFound:
            __version__ = 'unknown'
    except ImportError:
        __version__ = 'unknown'
