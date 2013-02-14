from __future__ import print_function, division, absolute_import
from fluenpy.parser import TextParser
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

def test_apache2():
    parser = TextParser()
    parser.configure({'format': 'apache2'})
    t, record = parser.parse('192.168.0.1 - - [27/Feb/2013:20:00:00 -0900] "GET / HTTP/1.1" 200 777 "-" "Opera/12.0"')
    tm = time.gmtime(t)
    assert tm.tm_year == 2013
    assert tm.tm_mon == 2
    assert tm.tm_mday == 28
    assert tm.tm_hour == 5
    assert record == {
            'user'   : None,
            'method' : 'GET',
            'code'   : 200,
            'size'   : 777,
            'host'   : '192.168.0.1',
            'path'   : '/',
            'referer': None,
            'agent'  : 'Opera/12.0'
            }

def test_syslog():
    parser = TextParser()
    parser.configure({'format': 'syslog'})
    t, record = parser.parse('Feb 28 12:00:00 192.168.0.1 fluentd[11111]: [error] Syslog test')
    tm = time.gmtime(t)
    now = time.gmtime()
    assert tm.tm_year == now.tm_year
    assert tm.tm_mon == 2
    assert tm.tm_mday == 28
    assert tm.tm_hour == 12
    assert tm.tm_min == 0
    assert tm.tm_sec == 0
    assert record == {
            'host'   : '192.168.0.1',
            'ident'  : 'fluentd',
            'pid'    : '11111',
            'message': '[error] Syslog test',
            }

def test_json():
    parser = TextParser()
    parser.configure({'format': 'json'})
    t, record = parser.parse('{"time":1362020400,"host":"192.168.0.1","size":777,"method":"PUT"}')
    assert t == 1362020400
    assert record == {
            'host'  : '192.168.0.1',
            'size'  : 777,
            'method': 'PUT',
            }

def test_nginx():
    parser = TextParser()
    parser.configure({'format': 'nginx'})
    t, record = parser.parse('127.0.0.1 192.168.0.1 - [28/Feb/2013:12:00:00 +0900] "GET / HTTP/1.1" 200 777 "-" "Opera/12.0"')
    tm = time.gmtime(t)
    assert (tm.tm_year, tm.tm_mon, tm.tm_mday) == (2013, 2, 28)
    assert (tm.tm_hour, tm.tm_min, tm.tm_sec) == (3, 0, 0)
    assert record == {
            'remote' : '127.0.0.1',
            'host'   : '192.168.0.1',
            'user'   : '-',
            'method' : 'GET',
            'path'   : '/',
            'code'   : '200',
            'size'   : '777',
            'referer': '-',
            'agent'  : 'Opera/12.0',
            }

def test_ltsv_config():
    parser = TextParser()
    parser.configure({'format': 'ltsv'})

    assert parser.parser.delimiter == '\t'
    assert parser.parser.label_delimiter == ':'

    parser.configure({
        'format': 'ltsv',
        'delimiter': ',',
        'label_delimiter': '=',
        })

    assert parser.parser.delimiter == ','
    assert parser.parser.label_delimiter == '='

def test_ltsv():
    parser = TextParser()
    parser.configure({'format': 'ltsv'})

    _, record = parser.parse("time:[28/Feb/2013:12:00:00 +0900]\thost:192.168.0.1\treq:GET /list HTTP/1.1")

    assert record == {
            'time':'[28/Feb/2013:12:00:00 +0900]',
            'host':'192.168.0.1',
            'req' :'GET /list HTTP/1.1',
            }

def test_ltsv_cosutomized_delimiter():
    parser = TextParser()
    parser.configure({'format': 'ltsv', 'delimiter':',', 'label_delimiter':'='})

    _, record = parser.parse('time=[28/Feb/2013:12:00:00 +0900],host=192.168.0.1,req=GET /list HTTP/1.1')

    assert record == {
            'time':'[28/Feb/2013:12:00:00 +0900]',
            'host':'192.168.0.1',
            'req' :'GET /list HTTP/1.1',
            }
