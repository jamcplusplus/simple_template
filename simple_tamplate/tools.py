import io
import re
import lxml
import zipfile
from cgi import escape


class Memory():
    def __init__(self):
        self.memory = io.BytesIO()

    def __get_data(self):
        self.memory.seek(0)
        return self.memory.read()

    def __save(self, out):
        with open(out, 'wb') as f:
            f.write(self.__get_data())
        return out

    def unzip_file(self, input_path):
        _z = zipfile.ZipFile(input_path)
        return {name: _z.read(name).decode('utf8') for name in _z.namelist()}

    def zip_file(self, static, output_path, extend=None):
        zf = zipfile.ZipFile(self.memory, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in static.iteritems():
            zf.writestr(k, v.encode('utf8'))
        if extend:
            for k, v in extend.iteritems():
                zf.write(v, k)
        return self.__save(out=output_path)


def safe_string(data):
    if isinstance(data, dict):
        for i in data.iterkeys():
            if isinstance(data[i], str):
                data[i] = escape(data[i])
            else:
                safe_string(data[i])
    if isinstance(data, list):
        for x, y in enumerate(data):
            if isinstance(y, str):
                data[x] = escape(y)
            else:
                safe_string(y)
    if isinstance(data, str):
        data = escape(data)
    return data

def max_rid(xml):
    _re = re.compile(r'rId\d+')
    return int(max(_re.findall(xml)).replace('rId', ''))
    