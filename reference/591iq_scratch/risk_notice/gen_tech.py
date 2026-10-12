"""技术通报 v2 → 可打印独立 HTML。复用 md2html.py 的 CSS 与骨架。"""
import io
import os
import re

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
SRC = os.path.join(D, "技术通报-v2.md")
DST = os.path.join(D, "技术通报-v2.html")

md = io.open(SRC, encoding="utf-8").read()

_css_src = io.open(os.path.join(D, "md2html.py"), encoding="utf-8").read()
CSS = re.search(r'CSS = """(.*?)"""', _css_src, re.S).group(1)
CSS += """
.note{margin:16px 0;padding:14px 18px;background:#fffaf0;
 border-left:3px solid var(--warn);border-radius:0 4px 4px 0;color:var(--ink2)}
.note .nt{font-weight:700;color:var(--warn);display:block;margin-bottom:4px}
.note ol,.note ul{margin:8px 0 2px 20px}
.note li{margin:4px 0;color:var(--ink)}
.warnbox{margin:16px 0;padding:14px 18px;background:#fdf3f2;
 border:1px solid #f0c4bf;border-left:4px solid var(--red);
 border-radius:0 4px 4px 0;color:var(--ink2)}
.warnbox .nt{font-weight:700;color:var(--red);display:block;margin-bottom:4px}
.riskbox{margin:16px 0;padding:14px 20px;background:#fdf3f2;
 border:1px solid #f0c4bf;border-left:4px solid var(--red);border-radius:0 4px 4px 0}
.riskbox table{margin:0}
.riskbox th{background:#fbe8e6}
.meta{font-size:13px;color:var(--ink2);margin:0 0 18px;line-height:1.9}
.meta b{color:var(--ink)}
h3{color:var(--blue)}
pre{font-size:12px}
@media print{.note,.warnbox,.riskbox{page-break-inside:avoid}}
"""


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"(https?://[^\s<，。）]+)", r'<a href="\1">\1</a>', t)
    return t


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue

        # 围栏代码块（必须先判，否则块内的 # 注释行会被当成 h1）
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="lang-%s"' % re.sub(r"\W+", "", lang) if lang else ""
            out.append("<pre%s><code>%s</code></pre>" % (cls, "\n".join(buf)
                       .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")))
            continue

        # 多行 callout
        if s.startswith(">"):
            buf, title = [], None
            while i < n and lines[i].strip().startswith(">"):
                body = re.sub(r"^\s*>\s?", "", lines[i])
                bs = body.strip()
                warn = "⚠" in bs[:4]
                # 先剥行首 emoji/⚠（不含 `*`，否则会吃掉加粗标记）
                bs2 = re.sub(r"^[\u2600-\u27bf\ufe0f\u200d\s]+", "", bs)
                m = re.match(r"^\*\*(.+?)\*\*", bs2)
                if title is None and m and not buf:   # 标题只认callout 首行
                    title = re.split(r"[：:，,。、]", m.group(1), 1)[0]
                    title = title.replace("*", "").strip() or None
                    rest = bs2[m.end():].lstrip("：: ").strip()
                    if rest:
                        buf.append(rest)
                elif title is None and warn and bs2 and not buf:
                    if re.search(r"[：:]", bs2):        # 首段作标题，冒号后作正文
                        head, tail_ = re.split(r"[：:]", bs2, 1)
                        title = head.strip() or None
                        if tail_.strip():
                            buf.append(tail_.strip())
                    else:                             # 无冒号：整句按逗号切
                        parts = re.split(r"[，,]", bs2, 1)
                        title = parts[0].strip() or None
                        if len(parts) > 1 and parts[1].strip():
                            buf.append(parts[1].strip())
                elif bs2:
                    buf.append(bs2)
                i += 1
            kind = "warnbox" if warn or (title and (
                "声明" in title or "澄清" in title)) else "note"
            inner, j = [], 0
            while j < len(buf):
                m = re.match(r"^(\d+)\.\s+(.*)$", buf[j])
                if m:
                    items = []
                    while j < len(buf):
                        m2 = re.match(r"^(\d+)\.\s+(.*)$", buf[j])
                        if not m2:
                            break
                        items.append("<li>%s</li>" % inline(m2.group(2)))
                        j += 1
                    inner.append("<ol>%s</ol>" % "".join(items))
                else:
                    inner.append("<p>%s</p>" % inline(buf[j]))
                    j += 1
            head = '<span class="nt">%s</span>' % inline(title) if title else ""
            out.append('<div class="%s">%s%s</div>' % (kind, head, "".join(inner)))
            continue

        # 表格
        if s.startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = [split_row(b) for b in block]
            head, body = rows[0], [
                r for r in rows[1:]
                if not all(re.fullmatch(r":?-{2,}:?", (c or "-").strip()) for c in r)]
            blank = all(not (c or "").strip() for c in head)
            cls = ' class="riskbox"' if blank else ""
            if blank:
                head = ["项", "内容"]
            out.append("<table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                cls,
                "".join("<th>%s</th>" % inline(c) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                        for r in body)))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue

        if re.fullmatch(r"-{3,}", s):
            out.append("<hr>")
            i += 1
            continue

        if s.startswith("**") and s.endswith("**") and "：" in s:
            buf = []
            while i < n:
                c2 = lines[i].strip()
                if not (c2.startswith("**") and c2.endswith("**")):
                    break
                k, v = c2.strip("*").split("：", 1)
                buf.append("<b>%s</b>：%s" % (inline(k.strip()), inline(v.strip())))
                i += 1
            out.append('<div class="meta">%s</div>' % "<br>".join(buf))
            continue

        if re.match(r"^[-*]\s+", s):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append("<li>%s</li>"
                             % inline(re.sub(r"^[-*]\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append("<li>%s</li>"
                             % inline(re.sub(r"^\d+\.\s+", "", lines[i].strip())))
                i += 1
            out.append("<ol>%s</ol>" % "".join(items))
            continue

        out.append("<p>%s</p>" % inline(s))
        i += 1
    return "\n".join(out)


body = render(md.split("\n"))

HTML = ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
        "<title>关于新壹我系统中两处越权访问问题的技术通报</title>\n"
        "<style>%s</style>\n</head>\n<body>\n<div class=\"sheet\">\n%s\n"
        "<div class=\"foot\">本文件为技术风险通报，含端点与实测数据，不构成法律意见。"
        "编号 RISK-2026-1006-01 · 2026-10-06 · 请勿外传至非技术岗位。</div>\n"
        "</div>\n</body>\n</html>\n") % (CSS, body)

io.open(DST, "w", encoding="utf-8", newline="").write(HTML)

h = io.open(DST, encoding="utf-8").read()
print("written -> %s (%d bytes)" % (DST, len(h.encode("utf-8"))))
print("h1=%d h2=%d h3=%d table=%d pre=%d note=%d warnbox=%d ol=%d ul=%d"
      % (h.count("<h1"), h.count("<h2"), h.count("<h3"), h.count("<table"),
         h.count("<pre"), h.count('class="note"'), h.count("warnbox"),
         h.count("<ol>"), h.count("<ul>")))
print("无外部资源:", h.count("<link") == 0 and "http-equiv" not in h)
print("含 noindex:", "noindex" in h)
print("端点齐全:", all(k in h for k in ("/search/search", "/record/queryRecordList",
                                  "/record/queryRecord")))
print("含 curl 复现:", h.count("curl") >= 2)
print("实测矩阵 146,021:", "146,021" in h)
print("口径澄清段:", "列表本身不返回身份字段" in h)
print("关键声明:", "不构成安全控制" in h)