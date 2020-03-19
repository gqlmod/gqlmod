"""
Provider machinery
"""
import contextlib
import contextvars
import collections
import functools

import pkg_resources
import graphql


__all__ = (
    'with_provider', 'exec_query', 'query_for_schema', 'get_additional_kwargs',
)

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
    Gets the current provider by name.
    """
    return _get_pmap()[name]


@contextlib.contextmanager
def with_provider(name, **params):
    """
    Uses a new instance of the provider (with the given parameters) for the
    duration of the context.
    """
    pmap = _get_pmap()
    newmap = pmap.copy()
    newmap[name] = load_provider_factory(name)(**params)
    token = provider_map.set(newmap)
    yield
    provider_map.reset(token)


@contextlib.contextmanager
def _mock_provider(name, instance):
    """
    Inserts and activates the given provider.

    FOR TEST INFRASTRUCTURE ONLY.
    """
    pmap = _get_pmap()
    newmap = pmap.copy()
    newmap[name] = instance
    token = provider_map.set(newmap)
    yield
    provider_map.reset(token)


def exec_query(provider, query, variables):
    """
    Executes a query with the given variables.

    NOTE: Some providers may expect additional variables. As this is an internal
    API, this is likely undocumented.
    """
    prov = get_provider(provider)
    return prov(query, variables)


@functools.lru_cache()
def query_for_schema(provider):
    """
    Asks the given provider for its schema
    """
    prov = get_provider(provider)
    if hasattr(prov, 'get_schema_str'):
        data = prov.get_schema_str()
        schema = graphql.build_schema(data)
    else:
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


# The GraphQL folks are arguing about doing this. I'm doing this to improve
# error messages.
def insert_builtins(schema):
    for scalar in BUILTIN_SCALARS:
        if not schema.get_type(scalar):
            schema = graphql.extend_schema(schema, graphql.parse(
                f"scalar {scalar}"
            ))
    return schema


def get_additional_kwargs(provider, gast, schema):
    """
    Gets the additional keywords to add to the query call, for codegen.
    """
    prov = get_provider(provider)
    if hasattr(prov, 'codegen_extra_kwargs'):
        return prov.codegen_extra_kwargs(gast, schema) or {}
    else:
        return {}
