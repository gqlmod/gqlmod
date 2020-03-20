"""
Helpers for using :py:mod:`aiohttp` to build a provider.

Requires the ``aiohttp`` extra.
"""
import aiohttp
import graphql


class AiohttpProvider:
    """
    Help build an HTTP-based provider based on aiohttp.

    You should fill in :py:attr:`endpoint` and possibly override
    :py:meth:`modify_request_args()`.
    """
    #: The URL to send requests to.
    endpoint: str

    #: Timeout policy to use, if any.
    timeout: aiohttp.ClientTimeout = None
    #: Whether a JSON-based or form-like request should be used.
    use_json: bool = False

    def modify_request_args(self, variables, kwargs):
        """
        Apply policies about the request, primarily authentication.
        """

    _session = None

    @property
    def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
            # Only needs to be a context manager for cleanup reasons.
        return self._session

    async def __call__(self, query, variables):
        payload = {
            'query': query,
            'variables': variables or {}
        }

        data_key = 'json' if self.use_json else 'data'

        kwargs = {
            'timeout': self.timeout,
            data_key: payload,
        }

        self.modify_request_args(variables, kwargs)

        resp = await self.session.post(self.endpoint, **kwargs)
        result = await resp.json()
        resp.raise_for_status()

        assert 'errors' in result or 'data' in result, 'Received non-compatible response "{}"'.format(result)
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )
