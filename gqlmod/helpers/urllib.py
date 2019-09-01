"""
Helpers for using urllib to build a provider. You probably want
UrllibJsonProvider.

Requires the no extras.
"""
import json
from urllib.request import urlopen, Request

import graphql


class UrllibProvider:
    """
    Help build an HTTP-based provider based on requests.

    You should fill-in endpoint and possibly overrirde modify_request()
    """
    endpoint: str

    def modify_request(self, req):
        """
        Apply policies about the request, primarily authentication.

        Accepts a urllib.request.Request object.
        """

    def _build_request(self, query, variables):
        raise NotImplementedError

    def __call__(self, query, variables):
        req = self._build_request(query, variables)

        self.modify_request(req)

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
    UrllibProvider that uses a JSON-based POST
    """
    def _build_request(self, query, variables):
        data = json.dumps({
            'query': query,
            'variables': variables,
        }, indent=4).encode('utf-8')
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