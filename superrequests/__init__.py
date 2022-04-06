__version__ = "0.1.0"

from requests.adapters import HTTPAdapter
from requests_toolbelt import sessions  # type: ignore
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 10  # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):  # pylint: disable=arguments-differ
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


default_retry_strategy = Retry(
    connect=3,
    read=3,
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)


class Session(sessions.BaseUrlSession):
    """
    Requests with sane defaults
    """

    def __init__(
        self,
        raise_for_status=True,
        timeout=5,
        retry_strategy=default_retry_strategy,
        **kwargs,
    ):
        super().__init__(**kwargs)

        adapter_kwargs = {}
        if retry_strategy:
            adapter_kwargs["max_retries"] = retry_strategy

        if timeout is not None:
            adapter_kwargs["timeout"] = timeout
            adapter = TimeoutHTTPAdapter(**adapter_kwargs)
            self.mount("http://", adapter)
            self.mount("https://", adapter)

        if raise_for_status:
            assert_status_hook = (
                lambda response, *args, **kwargs: response.raise_for_status()
            )
            self.hooks["response"] = [assert_status_hook]
