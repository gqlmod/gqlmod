import sys

from .importer import GqlLoader
from .providers import with_provider

__all__ = 'with_provider',


def enable_gql_import():
    """
    Enables importing .gql files.
    """
    sys.meta_path.append(GqlLoader())
