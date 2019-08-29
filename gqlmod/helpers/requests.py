"""
Helpers for using requests to build a provider.

Requires the requests extra.
"""
import requests
import graphql


class RequestsProvider:
    """
    Help build an HTTP-based provider based on requests.

    You should fill-in endpoint and possibly overrirde modify_request()
    """
    endpoint: str

    timeout = None
    use_json = False

    def modify_request(self, req):
        """
        Apply policies about the request, primarily authentication.

        Accepts a requests.Request object, and must return the same.
        """
        return req

    _session = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.session()
        return self._session

    def __call__(self, query, variables):
        payload = {
            'query': query,
            'variables': variables or {}
        }

        data_key = 'json' if self.use_json else 'data'

        resp = self.session.post(
            self.endpoint,
            timeout=self.timeout,
            auth=self.modify_request,
            verify=True,
            **{data_key: payload}
        )
        resp.raise_for_status()

        result = resp.json()
        assert 'errors' in result or 'data' in result, 'Received non-compatible response "{}"'.format(result)
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )
