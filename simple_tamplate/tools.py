import io
import re
import lxml
import zipfile
from cgi import escape


class Memory():
    'zip and unzip in memory'

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
        'unzip .zip file'
        _z = zipfile.ZipFile(input_path)
        return {name: _z.read(name).decode('utf8') for name in _z.namelist()}

    def zip_file(self, static, output_path, extend=None):
        'zip files'
        zf = zipfile.ZipFile(self.memory, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in static.iteritems():
            zf.writestr(k, v.encode('utf8'))
        if extend:
            for k, v in extend.iteritems():
                zf.write(v, k)
        return self.__save(out=output_path)


class StripRE(object):
    'strip broken tag'
    def __init__(self, xml):
        self.xml = xml

    def strip_var(self, m):
        """
        strip useless tag in vars. Like this:
        from:
            `<w:t>{{</w:t>
            </w:r>
            <w:r w:rsidR="001A7474">
                <w:t xml:space="preserve"> i</w:t>
            </w:r>
            <w:r>
                <w:rPr>
                    <w:rFonts w:hint="eastAsia"/>
                </w:rPr>
            <w:t>tem}}</w:t>`
        to:
            `<w:t>{{ item}}</w:t>`
        """
        txt = m.group()
        start = m.groups()[0]
        end = m.groups()[1]
        wrs = re.findall('<w:t[^>]*>.*?</w:t>', txt)  # tag with text
        return start + ''.join([re.sub('<[^>]*?>', '', i)
                                for i in wrs]) + end  # replace tag

    def tag_start(self, name='', reserve=False):
        if reserve:
            return r'(<{name}[^>]*?>)'.format(name=name)
        else:
            return r'<{name}[^>]*?>'.format(name=name)

    def tag_end(self, name='', reserve=False):
        if reserve:
            return r'(</{name}>)'.format(name=name)
        else:
            return r'</{name}>'.format(name=name)

    def format_jinja_template(self):
        REGX_TABLE = [
            (r"{(" + self.tag_start() + r"[\s\r\n]*)+({|%)", r"{\2"),
            # join the splited {{ or {%
            (r"}(" + self.tag_start() + r"[\s\r\n]*)+(%|})", r"}\2"),
            # replace logic control :
            (
                r"(" + self.tag_start("w:t") + ")[^<]*" + "{%" + "[^<}]*?(" +
                self.tag_end("w:t") + ")"
                # tag with "{%"
                r".*?"  # content in {% and %}
                r"" + self.tag_start("w:t") + "[^<{]*?" + "%}" + "[^<]*" +
                self.tag_end("w:t") + ""
                # tag with "%}"
                ,
                self.strip_var),
            # replace vars :
            (
                r"(" + self.tag_start("w:t") + ")[^<]*" + "{{" + "[^<}]*?(" +
                self.tag_end("w:t") + ")"
                # tag with "{{"
                r".*?"
                # content in {{ and }}
                r"" + self.tag_start("w:t") + "[^<{]*?" + "}}" + "[^<]*" +
                self.tag_end("w:t") + ""
                # tag with "}}"
                ,
                self.strip_var),
        ]
        txt = self.xml
        for regx, rep in REGX_TABLE:
            txt = re.sub(regx, rep, txt, flags=re.DOTALL)
        return txt


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
