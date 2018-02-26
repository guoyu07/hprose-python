import tornado.httpclient

from .client import HproseClient
from ..httpclient import (
    HproseHttpClient as OldHttpClient,
    _setCookie,
    _getCookie,
)
from ..common import NetErrorException


class HproseHttpClient(HproseClient, OldHttpClient):
    def __init__(self, uri=None):
        HproseClient.__init__(self, uri)
        OldHttpClient.__init__(self, uri)

    async def _sendAndReceive(self, data):
        header = {'Content-Type': 'application/hprose'}
        header['Host'] = self._host
        if self._port != 80:
            header['Host'] += ':' + str(self._port)
        cookie = _getCookie(self._host, self._path, self._scheme == 'https')
        if cookie != '':
            header['Cookie'] = cookie
        if self.keepAlive:
            header['Connection'] = 'keep-alive'
            header['Keep-Alive'] = str(self.keepAliveTimeout)
        else:
            header['Connection'] = 'close'
        for name in self._header:
            header[name] = self._header[name]

        httpclient = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest(
            url=self._uri,
            method='POST',
            headers=header,
            body=data,
            request_timeout=self.timeout,
        )
        # TODO 暂时不支持代理，因为需要tornado在启动时设置
        # AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        # 才行，条件过于苛刻
        try:
            response = await httpclient.fetch(request)
        except (tornado.httpclient.HTTPError, ConnectionRefusedError) as err:
            # TODO 需要将网络异常和逻辑异常分开处理
            raise NetErrorException(str(err))
        else:
            # 检查是否有set-Cookie头，需要缓存cookie用于下一次的通讯
            cookie_list = response.headers.get_list("set-cookie")  # type: list
            cookie_list.extend(response.headers.get_list("set-cookie2"))
            _setCookie(cookie_list, self._host)
            return response.body
