from fluenpy.parser import (
        TextParser,
        )
import time


def test_apache():
    parser = TextParser()
    parser.configure({'format': 'apache'})
    t, record = parser.parse('192.168.0.1 - - [28/Feb/2013:12:00:00 +0100] "GET / HTTP/1.1" 200 777')
    tm = time.gmtime(t)
    assert tm.tm_year == 2013
    assert tm.tm_mon == 2
    assert tm.tm_mday == 28
    assert tm.tm_hour == 11
    assert record == {
        'user': '-',
        'method': 'GET',
        'code': '200',
        'size': '777',
        'host': '192.168.0.1',
        'path': '/',
        }
