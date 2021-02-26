"""
Provider machinery
"""
import contextlib
import contextvars
import collections
import functools

try:
    import importlib.metadata as ilmd
except ImportError:
    import importlib_metadata as ilmd
import graphql

from .errors import MultiErrors


__all__ = (
    'with_provider', 'exec_query_sync', 'exec_query_async', 'query_for_schema',
    'get_additional_kwargs',
)

provider_map = contextvars.ContextVar('provider_map')


def load_provider_factory(name):
    """
    Queries the system for the given name.
    """
    try:
        # TODO: Warn if there's more than one?
        ep = next(ep for ep in ilmd.entry_points()['graphql_providers'] if ep.name == name)
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
        # This is if the contextvar hasn't been set yet
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


def _process_result(res):
    if isinstance(res, dict):
        # This will convert the response into the rich error type
        res = graphql.build_response(res)
        data = res.data
        errors = res.data
    elif isinstance(res, graphql.ExecutionResult):
        data = res.data
        errors = res.errors
    else:
        raise TypeError(
            f"Can't handle result of type {type(res)}. (This is probably a bug with the provider.)"
        )

    if errors:
        # Errors are present. Discard the data and raise those.
        # TODO: Map the error locations back to the source file's location
        assert len(errors) > 0
        if len(errors) == 1:
            raise errors[0]
        else:
            raise MultiErrors(errors)
    else:
        # No errors!
        return data


def exec_query_sync(provider, query, **variables):
    """
    Executes a query with the given variables. (Synchronous version)

    NOTE: Some providers may expect additional variables. As this is an internal
    API, this is likely undocumented.
    """
    prov = get_provider(provider)
    result = prov.query_sync(query, variables)
    return _process_result(result)


async def exec_query_async(provider, query, **variables):
    """
    Executes a query with the given variables. (Asynchronous version)

    NOTE: Some providers may expect additional variables. As this is an internal
    API, this is likely undocumented.
    """
    prov = get_provider(provider)
    result = await prov.query_async(query, variables)
    return _process_result(result)


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

        data = exec_query_sync(provider, query)
        schema = graphql.build_client_schema(data)
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
