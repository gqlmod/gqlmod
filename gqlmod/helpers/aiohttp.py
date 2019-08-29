"""
Helpers for using aiohttp to build a provider.

Requires the aiohttp extra.
"""
import aiohttp
import graphql


class AiohttpProvider:
    """
    Help build an HTTP-based provider based on aiohttp.

    You should fill-in endpoint and possibly overrirde modify_request_args()
    """
    endpoint: str

    timeout: aiohttp.ClientTimeout = None
    use_json: bool = False

    def modify_request_args(self, req):
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
            'verify': True,
            data_key: payload,
        }

        self.modify_request_args(kwargs)

        resp = await self.session.post(self.endpoint, **kwargs)
        resp.raise_for_status()

        result = await resp.json()
        assert 'errors' in result or 'data' in result, 'Received non-compatible response "{}"'.format(result)
        return graphql.ExecutionResult(
            errors=result.get('errors'),
            data=result.get('data')
        )
