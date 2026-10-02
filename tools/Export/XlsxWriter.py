"""极简 xlsx 写出器：纯标准库（zipfile + SpreadsheetML），零依赖。

只实现本项目导出需要的能力：多 sheet、表头填充色、斑马纹、冻结首行、
自动筛选、列宽、自动换行、超链接、数字格式、单元格边框。

对外 API：
    wb = Workbook()
    ws = wb.sheet("标题")
    ws.columns([("列名", 宽度), ...])
    ws.row([值, ...], style="data"|"zebra"|"head"|...)
    ws.freeze(1); ws.filter_row(1)
    wb.save(path)
"""

import zipfile
from xml.sax.saxutils import escape

# 调色板（ARGB）
C_HEADER_BG = "FF1F4E79"
C_HEADER_FG = "FFFFFFFF"
C_BAND_BG = "FFF2F7FB"
C_SECTION_BG = "FFDCE6F1"
C_KEY_BG = "FFEDF3FA"
C_TITLE_FG = "FF1F4E79"
C_BORDER = "FFB8CCE4"

# cellXfs 索引（顺序固定，勿乱改）
S_DEFAULT = 0
S_HEADER = 1
S_ZEBRA = 2
S_DATA = 3
S_WRAP = 4
S_WRAP_ZEBRA = 5
S_KEY = 6
S_TITLE = 7
S_SECTION = 8
S_LINK = 9
S_LINK_ZEBRA = 10
S_NUM = 11
S_NUM_ZEBRA = 12
S_CENTER = 13
S_CENTER_ZEBRA = 14
S_TOTAL = 15

_COLORS = {
    "hyperlink": "FF0563C1",
    "good": "FF1E7B34",
    "warn": "FF9C5700",
    "bad": "FFB00020",
}


def _fonts_xml():
    parts = [
        '<font><sz val="11"/><color theme="1"/><name val="等线"/><family val="2"/></font>',
        '<font><b/><sz val="11"/><color rgb="%s"/><name val="等线"/><family val="2"/></font>' % C_HEADER_FG,
        '<font><b/><sz val="14"/><color rgb="%s"/><name val="等线"/><family val="2"/></font>' % C_TITLE_FG,
        '<font><b/><sz val="11"/><color rgb="%s"/><name val="等线"/><family val="2"/></font>' % C_TITLE_FG,
        '<font><u/><sz val="11"/><color rgb="%s"/><name val="等线"/><family val="2"/></font>' % _COLORS["hyperlink"],
    ]
    for c in ("good", "warn", "bad"):
        parts.append('<font><b/><sz val="11"/><color rgb="%s"/><name val="等线"/>'
                     '<family val="2"/></font>' % _COLORS[c])
    return '<fonts count="%d">%s</fonts>' % (len(parts), "".join(parts))


def _fills_xml():
    parts = [
        '<fill><patternFill patternType="none"/></fill>',
        '<fill><patternFill patternType="gray125"/></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
        '<bgColor indexed="64"/></patternFill></fill>' % C_HEADER_BG,
        '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
        '<bgColor indexed="64"/></patternFill></fill>' % C_BAND_BG,
        '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
        '<bgColor indexed="64"/></patternFill></fill>' % C_SECTION_BG,
        '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
        '<bgColor indexed="64"/></patternFill></fill>' % C_KEY_BG,
    ]
    return '<fills count="%d">%s</fills>' % (len(parts), "".join(parts))


def _borders_xml():
    thin = '<%s style="thin"><color rgb="%s"/></%s>'
    side = "".join(thin % (t, C_BORDER, t) for t in ("left", "right", "top", "bottom"))
    parts = ['<border><left/><right/><top/><bottom/><diagonal/></border>',
             '<border>%s<diagonal/></border>' % side]
    return '<borders count="2">%s</borders>' % "".join(parts)


def _xf(idx, fontId=0, fillId=0, borderId=0, numFmtId=0, align=None):
    a = align or ""
    return ('<xf numFmtId="%d" fontId="%d" fillId="%d" borderId="%d" xfId="0"'
            ' applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
            '<alignment %s/></xf>' % (numFmtId, fontId, fillId, borderId, a))


def _styles_xml():
    wrap = 'horizontal="left" vertical="top" wrapText="1"'
    left = 'horizontal="left" vertical="center"'
    center = 'horizontal="center" vertical="center"'
    xfs = [
        _xf(0),                                                   # S_DEFAULT
        _xf(0, fontId=1, fillId=2, borderId=1, align=center),    # S_HEADER
        _xf(0, fillId=3, borderId=1, align=left),                 # S_ZEBRA
        _xf(0, borderId=1, align=left),                           # S_DATA
        _xf(0, borderId=1, align=wrap),                           # S_WRAP
        _xf(0, fillId=3, borderId=1, align=wrap),                 # S_WRAP_ZEBRA
        _xf(0, fontId=3, fillId=5, borderId=1, align=left),       # S_KEY
        _xf(0, fontId=2, align=left),                             # S_TITLE
        _xf(0, fontId=3, fillId=4, borderId=1, align=left),       # S_SECTION
        _xf(0, fontId=4, borderId=1, align=left),                 # S_LINK
        _xf(0, fontId=4, fillId=3, borderId=1, align=left),       # S_LINK_ZEBRA
        _xf(0, borderId=1, numFmtId=0, align='horizontal="right" vertical="center"'),
        _xf(0, fillId=3, borderId=1, align='horizontal="right" vertical="center"'),
        _xf(0, borderId=1, align=center),                         # S_CENTER
        _xf(0, fillId=3, borderId=1, align=center),               # S_CENTER_ZEBRA
        _xf(0, fontId=5, fillId=4, borderId=1,
            align='horizontal="right" vertical="center"'),        # S_TOTAL
    ]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<numFmts count="0"/>%s%s%s'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" '
            'borderId="0"/></cellStyleXfs>'
            '<cellXfs count="%d">%s</cellXfs>'
            '<cellStyles count="1"><cellStyle name="常规" xfId="0" builtinId="0"/>'
            '</cellStyles></styleSheet>'
            % (_fonts_xml(), _fills_xml(), _borders_xml(),
               len(xfs), "".join(xfs)))


def col_letter(idx):
    """0 -> A, 25 -> Z, 26 -> AA"""
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def cell_xml(ref, value, style, hyperlink=None):
    if value is None or value == "":
        return '<c r="%s" s="%d"/>' % (ref, style) if style else ""
    attrs = ' r="%s"' % ref
    if style:
        attrs += ' s="%d"' % style
    if isinstance(value, bool):
        return '<c%s t="b"><v>%d</v></c>' % (attrs, 1 if value else 0)
    if isinstance(value, (int, float)):
        return '<c%s><v>%s</v></c>' % (attrs, value)
    if hyperlink:
        return '<c%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' \
               % (attrs, escape(str(value)))
    return '<c%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' \
        % (attrs, escape(str(value)))


class Sheet:
    def __init__(self, name):
        self.name = name
        self.cols = []
        self.rows = []          # list of (list[(value, style, link)])
        self.freeze_row = 0
        self.filter_row = 0
        self.merges = []
        self.row_heights = {}
        self.hyperlinks = []    # (ref, url)

    def columns(self, spec):
        """spec: [(标题, 宽度), ...]"""
        self.cols = list(spec)

    def row(self, values, style=S_DATA, link_col=None, height=None):
        cells = []
        for i, v in enumerate(values):
            st = style
            if link_col is not None and i == link_col and isinstance(v, str) \
                    and v.startswith("http"):
                st = S_LINK if style in (S_DATA, S_CENTER) else S_LINK_ZEBRA
            if isinstance(v, int) and not isinstance(v, bool) \
                    and style in (S_DATA, S_ZEBRA):
                st = S_NUM if style == S_DATA else S_NUM_ZEBRA
            cells.append((v, st, None))
        self.rows.append(cells)

    def blank(self, style=S_DATA, n=None):
        n = n if n is not None else max(1, len(self.cols))
        self.rows.append([(None, style, None)] * n)

    def head(self, titles):
        self.row(titles, S_HEADER)
        self.row_heights[len(self.rows)] = 22

    def freeze(self, n=1):
        self.freeze_row = n

    def auto_filter(self, n=1):
        self.filter_row = n

    def total(self, values):
        self.row(values, S_TOTAL)

    def to_xml(self):
        cols = ""
        if self.cols:
            cs = "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>'
                         % (i + 1, i + 1, w) for i, (_, w) in enumerate(self.cols))
            cols = "<cols>%s</cols>" % cs
        sd = []
        if self.freeze_row:
            sd.append('<pane ySplit="%d" topLeftCell="A%d" activePane="bottomLeft"'
                      ' state="frozen"/>' % (self.freeze_row, self.freeze_row + 1))
            sd.append('<selection pane="bottomLeft" activeCell="A%d" sqref="A%d"/>'
                      % (self.freeze_row + 1, self.freeze_row + 1))
        body = []
        for ri, cells in enumerate(self.rows, 1):
            h = self.row_heights.get(ri)
            ra = ' ht="%s" customHeight="1"' % h if h else ""
            cs = []
            for ci, (v, st, _) in enumerate(cells):
                x = cell_xml("%s%d" % (col_letter(ci), ri), v, st)
                if x:
                    cs.append(x)
            body.append('<row r="%d"%s>%s</row>' % (ri, ra, "".join(cs)))
        dim = "A1:%s%d" % (col_letter(max(0, len(self.cols) - 1)),
                           max(1, len(self.rows)))
        af = ""
        if self.filter_row:
            last = col_letter(max(0, len(self.cols) - 1))
            af = ('<autoFilter ref="A%d:%s%d"/>'
                  % (self.filter_row, last, max(1, len(self.rows))))
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<dimension ref="%s"/><sheetViews><sheetView workbookViewId="0"'
                ' showGridLines="0">%s</sheetView></sheetViews>'
                '<sheetFormatPr defaultRowHeight="16"/>%s<sheetData>%s</sheetData>%s'
                '</worksheet>'
                % (dim, "".join(sd), cols, "".join(body), af))


class Workbook:
    def __init__(self):
        self.sheets = []

    def sheet(self, name):
        s = Sheet(name)
        self.sheets.append(s)
        return s

    def save(self, path):
        ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
              '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
        for i in range(1, len(self.sheets) + 1):
            ct.append('<Override PartName="/xl/worksheets/sheet%d.xml" '
                      'ContentType="application/vnd.openxmlformats-officedocument.'
                      'spreadsheetml.worksheet+xml"/>' % i)
        ct.append("</Types>")

        wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
              ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<sheets>%s</sheets></workbook>'
              % "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>'
                        % (escape(s.name), i, i)
                        for i, s in enumerate(self.sheets, 1)))

        wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  + "".join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                            'officeDocument/2006/relationships/worksheet" '
                            'Target="worksheets/sheet%d.xml"/>' % (i, i)
                            for i in range(1, len(self.sheets) + 1))
                  + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                    'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                    % (len(self.sheets) + 1)
                  + "</Relationships>")

        root = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                'officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                '</Relationships>')

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", "".join(ct))
            z.writestr("_rels/.rels", root)
            z.writestr("xl/workbook.xml", wb)
            z.writestr("xl/_rels/workbook.xml.rels", wbrels)
            z.writestr("xl/styles.xml", _styles_xml())
            for i, s in enumerate(self.sheets, 1):
                z.writestr("xl/worksheets/sheet%d.xml" % i, s.to_xml())
        return path