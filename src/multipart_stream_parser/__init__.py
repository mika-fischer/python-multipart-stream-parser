from collections import namedtuple

__version__ = "0.1.0"


class MultipartType(namedtuple('MultipartType',
                               ('subtype', 'boundary', 'parameters'))):
    """TODO"""

    pass


class Multipart(namedtuple('Multipart', ('headers', 'body'))):
    """TODO"""

    pass


class InvalidContentType(Exception):
    """TODO"""

    pass


def is_multipart(content_type):
    """TODO"""

    return content_type.startswith('multipart/')


def multipart_type(content_type, prepend_boundary_dashes=None):
    """TODO
    """

    if not is_multipart(content_type):
        raise InvalidContentType(
            'Not a multipart type: "{}"'.format(content_type))

    st_start = content_type.find('/')+1
    st_end = content_type.find(';')
    subtype = content_type[st_start:st_end]

    boundary = None
    parameters = {}
    for param in content_type[st_end+1:].strip().split():
        k, v = param.split('=', 1)
        if k == 'boundary':
            boundary = v
        else:
            parameters[k] = v

    if boundary is None:
        raise InvalidContentType(
            'boundary parameter is missing: "{}"'.format(content_type))

    if prepend_boundary_dashes or \
            (prepend_boundary_dashes is None and
             (not boundary.startswith('--') and
              len(boundary) > 2 and boundary[2] != '-')):
        boundary = '--' + boundary

    return MultipartType(subtype=subtype, boundary=boundary,
                         parameters=parameters)


def _find_pattern(pattern, buf, iterator, start=0):
    """Find pattern in buf, appending new data from iterator to buf if
    necessary
    """

    while len(buf) <= start + len(pattern):
        buf.extend(next(iterator))
    while True:
        pos = buf.find(pattern, start)
        if pos >= 0:
            assert pos >= start
            return pos
        else:
            start = len(buf) - len(pattern) - 1
            buf.extend(next(iterator))


def _read_headers(buf, iterator):
    """Read all headers, yield them, and remove them from buf"""

    start = 0
    while True:
        pos = _find_pattern(b'\r\n', buf, iterator, start)
        if pos == start:
            buf = buf[pos+2:]
            return
        else:
            k, v = buf[start:pos].decode('ascii').split(': ', maxsplit=1)
            yield k.title(), v
            start = pos + 2


def parse_parts(iterator, boundary):
    """TODO"""

    boundary = boundary.encode('ascii') + b'\r\n'
    buf = bytearray()
    pos = _find_pattern(boundary, buf, iterator)
    buf = buf[pos+len(boundary):]
    boundary = b'\r\n' + boundary

    while True:
        while len(buf) < 2:
            buf.extend(next(iterator))
        if buf[0:1] == b'--':
            return
        headers = dict(_read_headers(buf, iterator))

        # TODO: if content-lenght specified, preload data and check
        # for boundary there
        pos = _find_pattern(boundary, buf, iterator)

        newbuf = buf[pos+len(boundary):]
        yield Multipart(headers=headers, body=buf[:pos])
        buf = newbuf
