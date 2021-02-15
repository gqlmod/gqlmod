"""
The demo Star Wars graphql data set.

Purely local.
"""
from graphql import graphql_sync, graphql as graphql_async
from .schema import star_wars_schema


class StarWarsProvider:
    def query_sync(self, query, variables):
        return graphql_sync(star_wars_schema, query, variable_values=variables)

    async def query_async(self, query, variables):
        # Because this is all in-memory data, there isn't really benefit of async
        return await graphql_async(star_wars_schema, query, variable_values=variables)
