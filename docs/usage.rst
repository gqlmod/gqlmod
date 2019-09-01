Using gqlmod
============

Summary
-------
1. Install the ``gqlmod`` PyPI package, as well as any providers you need
2. Call :py:func:`gqlmod.enable_gql_import()` as soon as possible (maybe in your ``__main__.py`` or top-level ``__init__.py``)
3. Import your query file and start calling your queries.


Example
-------

.. code-block:: graphql
    :caption: queries.gql

    #~starwars~
    query HeroForEpisode($ep: Episode!) {
      hero(episode: $ep) {
        name
        ... on Droid {
          primaryFunction
        }
        ... on Human {
          homePlanet
        }
      }
    }


.. code-block:: python
    :caption: app.py
    
    import gqlmod
    gqlmod.enable_gql_import()

    from queries import HeroForEpisode

    resp = HeroForEpisode(ep='JEDI')
    assert not resp.errors

    print(resp.data)


