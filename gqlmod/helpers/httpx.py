"""
Helpers for using :py:mod:`httpx` to build a provider.

Requires the ``http`` extra.
"""
import json

import httpx
import graphql


class HttpxProvider:
    """
    Help build an HTTP-based provider based on httpx.

    You should fill in :py:attr:`endpoint` and possibly override
    :py:meth:`modify_request_args()`.
    """
    #: The URL to send requests to.
    endpoint: str

    #: Timeout policy to use, if any.
    timeout: httpx.Timeout = None

    _session_sync = None

    @property
    def session_sync(self):
        if self._session_sync is None:
            self._session_sync = httpx.Client()
            # Only needs to be a context manager for cleanup reasons.
        return self._session_sync

    _session_async = None

    @property
    def session_async(self):
        if self._session_async is None:
            self._session_async = httpx.AsyncClient()
            # Only needs to be a context manager for cleanup reasons.
        return self._session_async

    def build_request(self, query, variables):
        """
        Build the Request object.

        Override to add authentication and such.
        """
        data = json.dumps({
            'query': query,
            'variables': variables,
        }).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        return httpx.Request("POST", self.endpoint, content=data, headers=headers)

    def query_sync(self, query, variables):
        req = self.build_request(query, variables)

        resp = self.session_sync.send(req)
        result = resp.json()

        assert 'errors' in result or 'data' in result, f'Received non-compatible response "{result}"'
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )

    def query_async(self, query, variables):
        req = self.build_request(query, variables)

        resp = await self.session_sync.send(req)
        result = resp.json()

        assert 'errors' in result or 'data' in result, f'Received non-compatible response "{result}"'
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )
