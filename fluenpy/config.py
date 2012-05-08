import re
import os
from collections import namedtuple
from fluenpy.error import ConfigError, ConfigParserError

__all__ = 'Element Configurable config_param parse read'.split()

class Element(dict):
    def __init__(self, name, arg, attrs, elements, used=None):
        dict.__init__(self)
        self.name = name
        self.arg = arg
        self.elements = elements
        self.update(attrs)
        self.used = used or set()

    def add_element(name, arg=''):
        e = Element(name, arg, {}, [])
        self.elements.append(e)
        return e

    def __add__(self, o):
        attrs = self.attrs.copy()
        attrs.update(o)
        return Element(self.name, self.arg, attrs,
                       self.elements + o.elements,
                       self.used + o.used
                       )

    def __contains__(self, key):
        self.used.add(key)
        return dict.__contains__(self, key)

    def __getitem__(self, key):
        self.used.add(key)
        return dict.__getitem__(self, key)

    def get(self, k, D=None):
        self.used.add(k)
        return dict.get(self, k, D)

    def not_fetched(self):
        ret = []
        for key in self:
            if key not in self.used:
                ret.append((self,key))
        for child in self.elements:
            ret += child.not_fetched()
        return ret

    def _to_str(self, nest=0):
        indent = '  ' *nest
        nindent = '  ' *(nest+1)
        if self.arg:
            out = "%s<%s>\n" % (indent, self.name)
        else:
            out = "%s<%s %s>\n" % (indent, self.name, self.arg)

        for k,v in self.iteritems():
            out += "%s%s %s\n" % (nindent, k, v)

        for e in self.elements:
            out += e._to_str(nest+1)

        out += "%s</%s>\n" % (indent, self.name)
        return out

def _size_value(s):
    units = dict(k=1024, m=1024**2, g=1024**3, t=1024**4)
    m = re.match(r"([0-9]+)([kmgt])", s.lower())
    if m:
        return int(m.group(1)) * units[m.group(2)]
    else:
        return int(s)

def _time_value(s):
    units = dict(s=1, m=60, h=3600, d=3600*24)
    m = re.match(r"([0-9]+)([smhd])", s.lower())
    if m:
        return int(m.group(1)) * units[m.group(2)]
    else:
        return float(s)

def _bool_value(s):
    s = s.lower()
    if s in ('true', 'yes'):
        return True
    if s in ('false', 'no'):
        return False
    return None

def read(path):
    path = os.path.expanduser(os.path.expandvars(path))
    with open(path) as f:
        return parse(f, os.path.basename(path), os.path.dirname(path))

def parse(f, fname, basepath=None):
    if not basepath:
        basepath = os.getcwd()
    attrs, elems = Parser(basepath, f, fname).parse(True)
    return Element('ROOT', '', attrs, elems)


class Parser(object):
    def __init__(self, basepath, iterator, fname, line=0):
        self.basepath = basepath
        self.iterator = iter(iterator)
        self.line = line
        self.fname = fname

    def parse(self, allow_include, elem_name=None, attrs=None, elems=None):
        attrs = attrs or {}
        elems = elems or []
        end = "</%s>" % (elem_name,)

        for line in self.iterator:
            self.line += 1
            line = line.strip()
            line = line.split('#', 1)[0]
            if not line:
                continue
            if line == end:
                break

            m = re.match(r"\<([a-zA-Z0-9_]+)\s*(.+?)?\>$", line)
            if m:
                e_name = m.group(1)
                e_arg = m.group(2) or ""
                e_attrs, e_elems = self.parse(False, e_name)
                elems.append(Element(e_name, e_arg, e_attrs, e_elems))
                continue

            m = re.match(r"([a-zA-Z0-9_]+)\s*(.*)$", line)
            if m:
                key = m.group(1)
                val = m.group(2)
                if allow_include and key == 'include':
                    self.process_include(attrs, elems, val)
                else:
                    attrs[key] = val
                continue

            raise ConfigParseError("Parse error at %s line %s" % (self.fname, self.line))
        return attrs, elems

    def process_include(self, attrs, elems, uri):
        raise NotImplemented


_undef = []
_type_map = dict(string=str, integer=int, float=float,
                 size=_size_value, bool=_bool_value, time=_time_value,
                 )

class config_param(object):
    def __init__(self, type, default=_undef):
        self.default = default
        try:
            self.type = _type_map[type]
        except KeyError:
            raise ValueError("unknown config_param type %r" % (type,))


class Configurable(object):
    def configure(self, conf):
        kls = type(self)

        for varname in dir(kls):
            param = getattr(kls, varname)
            if not isinstance(param, config_param):
                continue
            if varname in conf:
                setattr(self, varname, param.type(conf[varname]))
            elif param.default is not _undef:
                setattr(self, varname, param.default)
            else:
                raise ConfigError("%r parameter is required" % (param.name,))
