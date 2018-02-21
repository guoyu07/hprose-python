import unittest
from python3.hprose.httpclient import _getCookie, _setCookie


class CookieTest(unittest.TestCase):
    def test_a(self):
        _setCookie(['a=1'], '127.0.0.1')
        cookie = _getCookie('127.0.0.1', '/a/b', False)
        print("cookie a: ", cookie)
        self.assertEqual(cookie, 'a=1')
        self.assertEqual(_getCookie('localhost', '/', False), '')
        _setCookie(['b=c; path=/c'], '127.0.0.1')
        print("cookie b: ", _getCookie('127.0.0.1', '/c', False))
        self.assertEqual(_getCookie('127.0.0.1', '/', False), 'a=1')
        self.assertEqual(_getCookie('127.0.0.1', '/c', False), 'a=1; b=c')
        self.assertEqual(_getCookie('127.0.0.1', '/c/d', False), 'a=1; b=c')
        self.assertEqual(_getCookie('127.0.0.1', '/d', False), 'a=1')


if __name__ == "__main__":
    unittest.main()
