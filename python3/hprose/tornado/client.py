import sys

from ..client import (
    HproseClient as OldClient,
)
from ..common import HproseResultMode

# 仅仅是为了type hint而引入
from tornado.gen import Future


class _AsyncInvoke(object):
    def __init__(self, invoke, name, args, callback, onerror, byref, resultMode, simple):
        self.__invoke = invoke
        self.__name = name
        self.__args = args
        self.__callback = callback
        self.__onerror = onerror
        self.__byref = byref
        self.__resultMode = resultMode
        self.__simple = simple

    async def __call__(self):
        future = self.__invoke(
            self.__name, self.__args, self.__byref,
            self.__resultMode, self.__simple)  # type: Future

        if hasattr(self.__callback, '__code__'):
            argcount = self.__callback.__code__.co_argcount
            if argcount == 0:
                future.add_done_callback(lambda f: self.__callback())
            elif argcount == 1:
                future.add_done_callback(lambda f: self.__callback(f.result()))
            else:
                future.add_done_callback(lambda f: self.__callback(f.result(), self.__args))
        else:
            future.add_done_callback(lambda f: self.__callback(f.result(), self.__args))

        def on_error(f):
            # type: (Future)->None
            if f.exception():
                self.__onerror(self.__name, f.exception())

        if self.__onerror is not None:
            future.add_done_callback(on_error)
        return await future


class _Method(object):
    def __init__(self, invoke, name):
        self.__invoke = invoke
        self.__name = name

    def __getattr__(self, name):
        return _Method(self.__invoke, self.__name + '_' + name)

    async def __call__(self, *args, **kargs):
        callback = kargs.get('callback', None)
        onerror = kargs.get('onerror', None)
        byref = kargs.get('byref', False)
        resultMode = kargs.get('resultMode', HproseResultMode.Normal)
        simple = kargs.get('simple', None)
        rt = await self.__invoke(self.__name, list(args), callback, onerror, byref, resultMode, simple)
        return rt


class HproseClient(OldClient):
    def __getattr__(self, name):
        return _Method(self.invoke, name)

    async def invoke(self, name, args=(), callback=None, onerror=None, byref=False,
                     resultMode=HproseResultMode.Normal, simple=None):
        """
        :param name: str
        :param args: List
        :param callback:
        :param onerror:
        :param byref: 是否为引用参数传递
            见 https://github.com/hprose/hprose-php/wiki/05.-Hprose-%E5%AE%A2%E6%88%B7%E7%AB%AF#byref-%E5%B1%9E%E6%80%A7
        :param resultMode:
            见 https://github.com/hprose/hprose-php/wiki/05.-Hprose-%E5%AE%A2%E6%88%B7%E7%AB%AF#mode
        :param simple: 是否为简单数据
            见 https://github.com/hprose/hprose-php/wiki/05.-Hprose-%E5%AE%A2%E6%88%B7%E7%AB%AF#simple-%E5%B1%9E%E6%80%A7
        :return:
        """
        if simple is None:
            simple = self.simple
        if callback is None:
            result = await self._invoke(name, args, byref, resultMode, simple)
            return result
        else:
            if isinstance(callback, str):
                callback = getattr(sys.modules['__main__'], callback, None)
            if not hasattr(callback, '__call__'):
                raise RuntimeError("callback must be callable")
            if onerror is None:
                onerror = self.onError
            if onerror is not None:
                if isinstance(onerror, str):
                    onerror = getattr(sys.modules['__main__'], onerror, None)
                if not hasattr(onerror, '__call__'):
                    raise RuntimeError("onerror must be callable")

            result = await _AsyncInvoke(
                self._invoke, name, args,
                callback, onerror, byref,
                resultMode, simple)()

            return result

    async def _invoke(self, name, args, byref, resultMode, simple):
        data = self._doOutput(name, args, byref, simple)
        recv = await self._sendAndReceive(data)
        return self._doInput(recv, args, resultMode)
