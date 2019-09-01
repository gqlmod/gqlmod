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

