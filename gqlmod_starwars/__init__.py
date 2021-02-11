"""
The demo Star Wars graphql data set.

Purely local.
"""
from graphql import graphql_sync
from .schema import star_wars_schema


class StarWarsProvider:
    def query_sync(self, query, variables):
        return graphql_sync(star_wars_schema, query, variable_values=variables)
