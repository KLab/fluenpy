from fluenpy.config import *
import io


def test_parse():
    sample = """
# This is comment.

<sec1>
    foo bar
    fizz buzz
    <sec11>
        foo bar
    </sec11>
    <sec11>
        fizz buzz
    </sec11>
</sec1>

<sec2 hoge>
    hage hige
</sec2>
"""
    f = io.BytesIO(sample)
    elem = parse(f, "sample.conf")
    assert elem.name == 'ROOT'
    assert elem.arg == ''
    assert not elem
    assert len(elem.elements) == 2
    assert elem.elements[0].name == 'sec1'
    assert elem.elements[0] == {'foo': 'bar', 'fizz': 'buzz'}
    subelems = elem.elements[0].elements
    assert len(subelems) == 2
    assert subelems[0].name == 'sec11'
    assert subelems[1].name == 'sec11'
    assert elem.elements[1].name == 'sec2'


def test_configurable():
    class Foo(Configurable):
        s = config_param('string')
        i = config_param('integer')
        f = config_param('float')

    class Bar(Foo):
        sz1 = sz2 = sz3 = sz4 = sz5 = config_param('size')
        b1 = b2 = b3 = b4 = config_param('bool')
        t1 = t2 = t3 = t4 = t5 = config_param('time')

    sample = """
<sec1>
    s xyzzy
    i 123
    f 123.5
    sz1 10
    sz2 10k
    sz3 10m
    sz4 10g
    sz5 10t
    b1 true
    b2 yes
    b3 false
    b4 no
    t1 10
    t2 10s
    t3 10m
    t4 10h
    t5 10d
</sec1>
"""
    f = io.BytesIO(sample)
    elem = parse(f, "sample.conf")
    bar = Bar()
    bar.configure(elem.elements[0])

    assert type(bar.s) == str
    assert bar.s == 'xyzzy'

    assert type(bar.i) == int
    assert bar.i == 123

    assert type(bar.f) == float
    assert bar.f == 123.5

    assert type(bar.sz1) == int
    assert bar.sz1 == 10
    assert bar.sz2 == 10240
    assert bar.sz3 == 1024**2 * 10
    assert bar.sz4 == 1024**3 * 10
    assert bar.sz5 == 1024**4 * 10

    assert bar.b1 is True
    assert bar.b2 is True
    assert bar.b3 is False
    assert bar.b4 is False

    assert bar.t1 == 10
    assert bar.t2 == 10
    assert bar.t3 == 600
    assert bar.t4 == 36000
    assert bar.t5 == 10 * 24 * 3600


def test_default():
    class Foo(Configurable):
        s = t = config_param('string', default='abc')

    sample = """
<sec1>
    s xyzzy
</sec1>
"""
    f = io.BytesIO(sample)
    elem = parse(f, "sample.conf")
    foo = Foo()
    foo.configure(elem.elements[0])

    assert foo.s == 'xyzzy'
    assert foo.t == 'abc'
