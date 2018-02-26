import logging
import time
import tornado.testing
import tornado.web
import tornado.gen
import tornado.wsgi
import python3.hprose as hprose
from python3.hprose.tornado import httpclient

logger = logging.getLogger(__name__)
for handle in logger.handlers:
    handle.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)


def hello(name):
    return 'Hello %s!' % name


def error(name):
    raise RuntimeError('{} 异常测试'.format(name))


service = hprose.HttpService()
service.addFunction(hello)
service.addFunction(error)


class TestHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        # hprose的service只接受wsgi的environ，因此需要将request对象转为environ对象再传给hprose处理
        environ = tornado.wsgi.WSGIContainer.environ(self.request)
        status, headers, body = service(environ)
        # 返回响应
        self.set_status(int(status.split(' ')[0]))
        for name, value in headers:
            self.add_header(name, value)
        yield tornado.gen.sleep(1)
        self.finish(body[0])

    @tornado.gen.coroutine
    def post(self):
        # hprose的service只接受wsgi的environ，因此需要将request对象转为environ对象再传给hprose处理
        environ = tornado.wsgi.WSGIContainer.environ(self.request)
        logger.debug('request cookies:{}'.format(self.cookies))
        logger.debug('cookie a: {}'.format(self.get_cookie('a', '***')))
        logger.debug('cookie bbb: {}'.format(self.get_cookie('bbb', '***')))
        status, headers, body = service(environ)
        # 返回响应
        self.set_status(int(status.split(' ')[0]))
        for name, value in headers:
            self.add_header(name, value)
        yield tornado.gen.sleep(1)
        self.finish(body[0])
        logger.debug('请求完成')


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/hprose", TestHandler),
        ]
        settings = dict(
            xsrf_cookies=False,
        )
        super(Application, self).__init__(handlers, **settings)


class HttpClientTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return Application()

    def test_http_fetch(self):
        response = self.fetch('/hprose')
        # response = yield self.http_client.fetch(self.get_url('/'))
        logger.debug(response.body)
        self.assertEqual(response.code, 200)
        self.assertIn("hello", response.body.decode())

    @tornado.testing.gen_test
    async def test_hprose(self):
        try:
            rpc_client = httpclient.HproseHttpClient(uri=self.get_url("/hprose"))
            arg = "world"
            rt = await rpc_client.hello(arg)
            logger.debug(rt)
            self.assertIn(arg, rt)
        finally:
            self.stop()

    @tornado.testing.gen_test
    async def test_muti(self):
        try:
            rpc_client = httpclient.HproseHttpClient(uri=self.get_url("/hprose"))
            arg = "world"
            # 多个请求并行
            start = time.time()
            f1 = rpc_client.hello(arg)
            f2 = rpc_client.hello(arg)
            f3 = rpc_client.hello(arg)
            rt = await tornado.gen.multi([f1, f2, f3])
            logger.debug(rt)
            self.assertIn(arg, rt[0])
            self.assertLess(time.time() - start, 2)
        finally:
            self.stop()

    @tornado.testing.gen_test
    async def test_error(self):
        try:
            # 服务方主动抛出的异常
            with self.assertRaises(hprose.common.ServiceException):
                rpc_client = httpclient.HproseHttpClient(uri=self.get_url("/hprose"))
                arg = "aaa"
                rt = await rpc_client.error(arg)
                logger.debug(rt)
                self.assertIn(arg, rt)

            # 不存在的方法
            with self.assertRaises(hprose.common.ServiceException):
                rpc_client = httpclient.HproseHttpClient(uri=self.get_url("/hprose"))
                arg = "aaa"
                rt = await rpc_client.aaa(arg)
                logger.debug(rt)
                self.assertIn(arg, rt)

            # 端口错误
            with self.assertRaises(hprose.common.NetErrorException):
                rpc_client = httpclient.HproseHttpClient(uri='http://localhost:8888/hprose')
                arg = "aaa"
                rt = await rpc_client.hello(arg)
                logger.debug(rt)
                self.assertIn(arg, rt)
        finally:
            self.stop()


if __name__ == "__main__":
    tornado.testing.main()
