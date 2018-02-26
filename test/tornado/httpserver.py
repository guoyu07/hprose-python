import tornado.testing
import tornado.web
import tornado.gen
import tornado.wsgi
import tornado.util

if tornado.util.PY3:
    from python3 import hprose
else:
    from python2 import hprose


def hello(name):
    return 'Hello %s!' % name


service = hprose.HttpService()
service.addFunction(hello)


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
        yield tornado.gen.sleep(2)
        self.finish(body[0])

    @tornado.gen.coroutine
    def post(self):
        # hprose的service只接受wsgi的environ，因此需要将request对象转为environ对象再传给hprose处理
        environ = tornado.wsgi.WSGIContainer.environ(self.request)
        status, headers, body = service(environ)
        # 返回响应
        self.set_status(int(status.split(' ')[0]))
        for name, value in headers:
            self.add_header(name, value)
        yield tornado.gen.sleep(2)
        self.finish(body[0])


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", TestHandler),
        ]
        settings = dict(
            xsrf_cookies=False,
        )
        super(Application, self).__init__(handlers, **settings)


class HttpServerTest(tornado.testing.AsyncTestCase):
    def test_start_server(self):
        pass


if __name__ == "__main__":
    tornado.testing.main()
    import tornado.ioloop

    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
