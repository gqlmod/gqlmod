"""
Helpers for using urllib to build a provider. You probably want
:py:class:`UrllibJsonProvider`.

Requires the no extras.
"""
import json
from urllib.request import urlopen, Request

import graphql


class UrllibProvider:
    """
    Help build an HTTP-based provider based on requests.

    You should fill in :py:attr:`endpoint` and possibly override
    :py:meth:`modify_request()`.
    """
    #: The URL to send requests to
    endpoint: str

    def modify_request(self, req, variables):
        """
        Apply policies about the request, primarily authentication.

        Accepts a :py:class:`urllib.request.Request` object.
        """

    def build_request(self, query, variables):
        raise NotImplementedError

    def __call__(self, query, variables):
        req = self.build_request(query, variables)

        self.modify_request(req, variables)

        resp = urlopen(req)
        text = resp.read().decode('utf-8')  # JSON must be UTF-8
        result = json.loads(text)

        assert 'errors' in result or 'data' in result, 'Received non-compatible response "{}"'.format(result)
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )


class UrllibJsonProvider(UrllibProvider):
    """
    A :py:class:`UrllibProvider` that uses a JSON-based POST
    """
    def build_request(self, query, variables):
        data = json.dumps({
            'query': query,
            'variables': variables,
        }).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
        }

        return Request(self.endpoint, method='POST', data=data, headers=headers)


# TODO: Implement this. The big problem is that it's not super clear how
#       JSON-ish data should map to x-www-form-urlencoded
# See: https://docs.python.org/3/library/urllib.request.html#urllib.request.Request
# class UrllibFormProvider(UrllibProvider):
#     """
#     UrllibProvider that uses a form-based POST
#     """
