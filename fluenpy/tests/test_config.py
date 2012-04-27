from fluenpy.config import *
import io

_sample = """
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

def test_parse():
    f = io.BytesIO(_sample)
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
