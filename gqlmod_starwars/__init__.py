from graphql import graphql_sync
from .schema import star_wars_schema


class StarWarsProvider:
    def __call__(self, query, variables):
        # TODO: Convert to data/exception
        result = graphql_sync(star_wars_schema, query, variable_values=variables)
        assert not result.errors
        return result.data
