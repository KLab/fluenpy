from fluenpy.parser import (
        ApacheParser,
        )
import time


def test_apache():
    parser = ApacheParser()
    t, record = parser('192.168.0.1 - - [28/Feb/2013:12:00:00 +0900] "GET / HTTP/1.1" 200 777')
    tm = time.gmtime(t)
    assert tm.tm_year == 2013
    assert tm.tm_mon == 2
    assert tm.tm_mday == 28
    assert tm.tm_hour == 12-9
    assert record == {
        'user': '-',
        'method': 'GET',
        'code': '200',
        'size': '777',
        'host': '192.168.0.1',
        'path': '/',
        }
