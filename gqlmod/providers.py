"""
Provider machinery
"""
import contextlib
import contextvars
import collections
import functools

import pkg_resources
import graphql

provider_map = contextvars.ContextVar('provider_map')


def load_provider_factory(name):
    """
    Queries the system for the given name.
    """
    try:
        # TODO: Warn if there's more than one?
        ep = next(pkg_resources.iter_entry_points('graphql_providers', name))
        return ep.load()
    except StopIteration:
        raise ValueError(f"{name} is not a registered provider")


class ProviderDict(collections.defaultdict):
    def __missing__(self, key):
        factory = load_provider_factory(key)
        inst = factory()
        self[key] = inst
        return inst


def _get_pmap():
    try:
        pmap = provider_map.get()
    except LookupError:
        pmap = ProviderDict()
        provider_map.set(pmap)
    return pmap


def get_provider(name):
    """
    Gets the current provider for name.
    """
    return _get_pmap()[name]


@contextlib.contextmanager
def with_provider(name, **params):
    """
    Uses a new instances of the provider (with the given parameters) for the
    duration of the context.
    """
    pmap = _get_pmap()
    newmap = pmap.copy()
    newmap[name] = load_provider_factory(name)(**params)
    token = provider_map.set(newmap)
    yield
    provider_map.reset(token)


def exec_query(provider, query, variables):
    prov = get_provider(provider)
    return prov(query, variables)


@functools.lru_cache()
def query_for_schema(provider):
    """
    Asks the given provider for its schema
    """
    query = graphql.get_introspection_query(descriptions=True)
    res = exec_query(provider, query, {})
    assert not res.errors
    schema = graphql.build_client_schema(res.data)
    schema = insert_builtins(schema)
    return schema


BUILTIN_SCALARS = (
    'Int',
    'Float',
    'String',
    'Boolean',
    'ID',
)


# The GraphQL folks are arguing about to do this. I'm doing this to improve
# error messages.
def insert_builtins(schema):
    for scalar in BUILTIN_SCALARS:
        if not schema.get_type(scalar):
            schema = graphql.extend_schema(schema, graphql.parse(
                f"scalar {scalar}"
            ))
    return schema
