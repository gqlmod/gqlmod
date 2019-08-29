"""
Implementation of functions used by compiled modules
"""
from .providers import exec_query


def __query__(provider, query, **variables):
    return exec_query(provider, query, variables)
