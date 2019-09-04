Writing a Provider
==================

Writing a provider is fairly staightforward.

1. Define a provider class
2. Add an entry point declaration


Provider Classes
----------------

A provider class is only required to be callable with a specific signature.


.. code-block:: python
    
    import graphql


    class MyProvider:
        def __init__(self, token=None):
            self.token = token

        def __call__(self, query, variables):
            # Do stuff here

            return graphql.ExecutionResult(
                errors=[],
                data={'spam': 'eggs'}
            )

The arguments it takes are:

* ``query``: (string) The query to give to the server
* ``variables``: (dict) The variables for that query

The provider should return a :py:class:`graphql.ExecutionResult` as shown above.


Entry point
-----------

In order to be discoverable by gqlmod, providers must define entrypoints. 
Specifically, in the ``graphql_providers`` group under the name you want ``.gql``
files to use. This can take a few different forms, depending on your project. A few examples:

.. code-block:: ini
    :caption: setup.cfg

    [options.entry_points]
    graphql_providers =
        starwars = gqlmod_starwars:StarWarsProvider


.. code-block:: python
    :caption: setup.py

    setup(
        # ...
        entry_points={
            'graphql_providers': [
                'starwars = gqlmod_starwars:StarWarsProvider'
            ]
        },
        # ...
    )


.. code-block:: toml
    :caption: pyproject.toml

    # This is for poetry-based projects
    [tool.poetry.plugins.graphql_providers]
    "starwars" = "gqlmod_starwars:StarWarsProvider'"


Helpers
-------

In order to help with common cases, gqlmod ships with several helpers

Note that many of them have additional requirements, which are encapsulated in extras.


urllib
~~~~~~

.. automodule:: gqlmod.helpers.urllib
   :members:


aiohttp
~~~~~~~

.. automodule:: gqlmod.helpers.aiohttp
   :members:


Extensions
----------

In addition to the core querying interface, providers may influence the import 
process in a few different ways. These are all implemented as optional methods
on the provider instance.


``get_schema_str()``
~~~~~~~~~~~~~~~~~~~~

Providers may override the standard schema discovery mechanism by implementing
``get_schema_str()``. This is useful for providers that don't have a primary 
service or don't allow anonymous access at all.

This method must be synchronous. An async variation is not supported.

**Default behavior**: Issue a GraphQL introspection query via the standard query
path.

**Parameters**: None.

**Returns**: A :py:class:`str` of the schema, in standard GraphQL schema
language.


``codegen_extra_kwargs()``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Providers may add keyword arguments (variables) to the query call inside the
generated module. These will be passed through the query pipeline back to the
provider.

**Default behavior**: No additional variables are inserted.

**Parameters**:

* ``graphql_ast`` (positional, :py:class:`graphql.language.OperationDefinitionNode`): The AST of the GraphQL query in question
* ``schema`` (positional, :py:class:`graphql.type.GraphQLSchema`): The schema of the service

**Returns**: A :py:class:`dict` of the names mapping to either simple values or
:py:class:`ast.AST` instances. (Note that the returned AST will be embedded into
a right-hand expression context.)
