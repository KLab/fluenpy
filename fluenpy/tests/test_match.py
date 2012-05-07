from fluenpy.match import *


def test_match():
    m = Match("foo.* *.bar", None)
    assert m.match('foo.xxx')
    assert not m.match('foo')
    assert m.match('xxx.bar')
    assert not m.match('bar')
    assert not m.match('fooo.xxx')
    assert m.match('fooo.bar')
