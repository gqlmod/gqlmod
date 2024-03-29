import sys

from .importer import GqlLoader
from .providers import with_provider

__all__ = 'with_provider', 'enable_gql_import'


def enable_gql_import():
    """
    Enables importing ``.gql`` files.

    Importing :py:mod:`gqlmod.enable` calls this.
    """
    sys.meta_path.append(GqlLoader())
