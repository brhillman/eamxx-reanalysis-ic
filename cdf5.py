"""
Direct, concurrent writes into a CDF5 (NETCDF3_64BIT_DATA) file.

The file is created and its header written once with netCDF4 (fill off).
Workers then write disjoint column ranges of each variable at byte offsets
taken from the header, with os.pwrite. In the classic formats each
variable's data is one contiguous, big-endian block starting at its 'begin'
offset (for record variables with exactly one record, likewise), and the
IC variables are laid out (time, ncol, ...), so a column range is one
contiguous byte range. Workers never touch the header, so no locking or
MPI-IO is needed. Readback through netCDF4 is checked by the driver.
"""
import os
import struct

_TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 4, 6: 8, 7: 1, 8: 2, 9: 4, 10: 8, 11: 8}
_TYPE_DTYPE = {3: '>i2', 4: '>i4', 5: '>f4', 6: '>f8', 10: '>i8'}
NC_DIMENSION, NC_VARIABLE, NC_ATTRIBUTE = 10, 11, 12


class _Reader:
    def __init__(self, buf):
        self.b, self.o = buf, 0

    def i32(self):
        v = struct.unpack_from('>i', self.b, self.o)[0]; self.o += 4; return v

    def i64(self):
        v = struct.unpack_from('>q', self.b, self.o)[0]; self.o += 8; return v

    def name(self):
        n = self.i64()
        s = self.b[self.o:self.o + n].decode()
        self.o += (n + 3) // 4 * 4
        return s

    def skip_atts(self):
        tag, n = self.i32(), self.i64()
        if tag not in (0, NC_ATTRIBUTE):
            raise ValueError('bad attribute list tag')
        for _ in range(n):
            self.name()
            t, ne = self.i32(), self.i64()
            self.o += (ne * _TYPE_SIZE[t] + 3) // 4 * 4


def read_layout(path, header_bytes=1 << 24):
    """Return (dims {name: length}, numrecs, vars {name: dict(dims, type,
    vsize, begin)}) from a CDF5 header."""
    with open(path, 'rb') as f:
        buf = f.read(header_bytes)
    r = _Reader(buf)
    if buf[:4] != b'CDF\x05':
        raise ValueError(f'{path} is not CDF5')
    r.o = 4
    numrecs = r.i64()
    dims = []
    tag, n = r.i32(), r.i64()
    if tag not in (0, NC_DIMENSION):
        raise ValueError('bad dimension list tag')
    for _ in range(n):
        dims.append((r.name(), r.i64()))
    r.skip_atts()
    tag, n = r.i32(), r.i64()
    if tag not in (0, NC_VARIABLE):
        raise ValueError('bad variable list tag')
    vars_ = {}
    for _ in range(n):
        name = r.name()
        nd = r.i64()
        dimids = [r.i64() for _ in range(nd)]
        r.skip_atts()
        t, vsize, begin = r.i32(), r.i64(), r.i64()
        vars_[name] = dict(dims=[dims[d][0] for d in dimids], type=t,
                           vsize=vsize, begin=begin)
    return dict(dims), numrecs, vars_


class ColumnWriter:
    """Write column ranges of (time, ncol, ...) or (ncol, ...) variables."""

    def __init__(self, path):
        self.dims, self.numrecs, self.vars = read_layout(path)
        self.fd = os.open(path, os.O_WRONLY)

    def write(self, name, col0, data):
        v = self.vars[name]
        d = [x for x in v['dims'] if x != 'time']
        if d[0] != 'ncol':
            raise ValueError(f'{name}: first non-time dimension is not ncol')
        row = 1
        for x in d[1:]:
            row *= self.dims[x]
        if data.size != data.shape[0] * row:
            raise ValueError(f'{name}: data shape {data.shape} vs row length {row}')
        buf = memoryview(data.astype(_TYPE_DTYPE[v['type']], copy=False).tobytes())
        off = v['begin'] + col0 * row * _TYPE_SIZE[v['type']]
        while len(buf):
            k = os.pwrite(self.fd, buf, off)
            buf, off = buf[k:], off + k

    def close(self):
        os.fsync(self.fd)
        os.close(self.fd)
