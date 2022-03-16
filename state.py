from .log2 import floor_log2
from threading import local


class State(local):
    # thread local so unit tests can be run in parallel without breaking
    def __init__(self, *, XLEN=64, GFBREDPOLY=0, GFPRIME=31):
        assert isinstance(XLEN, int) and 2 ** floor_log2(XLEN) == XLEN
        assert isinstance(GFBREDPOLY, int) and 0 <= GFBREDPOLY < 2 ** 64
        assert isinstance(GFPRIME, int) and 0 <= GFPRIME < 2 ** 64
        self.XLEN = XLEN
        self.GFBREDPOLY = GFBREDPOLY
        self.GFPRIME = GFPRIME

    def reinit(self, *, XLEN=64, GFBREDPOLY=0, GFPRIME=31):
        self.__init__(XLEN=XLEN, GFBREDPOLY=GFBREDPOLY, GFPRIME=GFPRIME)


ST = State()
