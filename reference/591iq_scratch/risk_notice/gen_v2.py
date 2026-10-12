"""学生会版 v2 → 可打印独立 HTML。

复用 md2html.py 的样式与页面骨架，但自己写转换循环：
v2 里有**多行 callout（含嵌套有序列表）**，md2html.py 的 blockquote 是逐行处理，
会把同一段引言拆成四个独立块、且里面的 "1. 2. 3. 4." 变成正文，所以必须重写。
"""
import io
import os
import re

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
SRC = os.path.join(D, "学生会版-v2.md")
DST = os.path.join(D, "学生会版-v2.html")

md = io.open(SRC, encoding="utf-8").read()

# 复用既有渲染器的 CSS，避免样式漂移
_css_src = io.open(os.path.join(D, "md2html.py"), encoding="utf-8").read()
CSS = re.search(r'CSS = """(.*?)"""', _css_src, re.S).group(1)
CSS += """
.note{margin:16px 0;padding:14px 18px;background:#fffaf0;
 border-left:3px solid var(--warn);border-radius:0 4px 4px 0;color:var(--ink2)}
.note .nt{font-weight:700;color:var(--warn);display:block;margin-bottom:4px}
.note ol{margin:8px 0 2px 20px}
.note li{margin:4px 0;color:var(--ink)}
.riskbox{margin:16px 0;padding:16px 20px;background:#fdf3f2;
 border:1px solid #f0c4bf;border-left:4px solid var(--red);border-radius:0 4px 4px 0}
.riskbox table{margin:0}
.riskbox th{background:#fbe8e6}
.meta{font-size:13px;color:var(--ink2);margin:0 0 18px;line-height:1.9}
.meta b{color:var(--ink)}
@media print{.note,.riskbox{page-break-inside:avoid}}
"""


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', t)
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

        # --- 多行 callout：连续的 "> " 归为一个 note ---
        if s.startswith(">"):
            buf, title = [], None
            while i < n and lines[i].strip().startswith(">"):
                body = re.sub(r"^\s*>\s?", "", lines[i])
                if body.strip().startswith("**") and body.strip().endswith("**"):
                    title = body.strip().strip("*")
                elif body.strip():
                    buf.append(body.strip())
                i += 1
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
            out.append('<div class="note">%s%s</div>' % (head, "".join(inner)))
            continue

        # --- 表格 ---
        if s.startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = [split_row(b) for b in block]
            head, body = rows[0], [
                r for r in rows[1:]
                if not all(re.fullmatch(r":?-{2,}:?", (c or "-").strip()) for c in r)]
            # 空表头的两列表，转成 riskbox（定级表）
            blank_head = all(not (c or "").strip() for c in head)
            cls = ' class="riskbox"' if blank_head else ""
            if blank_head:
                head = ["项", "内容"]
            else:
                cls = ""
            out.append("<table%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                cls,
                "".join("<th>%s</th>" % inline(c) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                        for r in body)))
            continue

        # --- 标题 ---
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

        # --- 元信息块（**提给**：… 连续行）→ .meta ---
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

        # --- 列表：连续项合并成 ul / ol ---
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append("<li>%s</li>"
                             % inline(re.sub(r"^[-*]\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
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
        "<title>关于新壹我系统中两处越权访问问题的说明（学生会版）</title>\n"
        "<style>%s</style>\n</head>\n<body>\n<div class=\"sheet\">\n%s\n"
        "<div class=\"foot\">本文为技术风险通报的通俗版本，不构成法律意见。"
        "编号 RISK-2026-1006-01（学生会版） · 2026-10-06 · 本件不含技术细节。</div>\n"
        "</div>\n</body>\n</html>\n") % (CSS, body)

io.open(DST, "w", encoding="utf-8", newline="").write(HTML)

h = io.open(DST, encoding="utf-8").read()
print("written -> %s (%d bytes)" % (DST, len(h.encode("utf-8"))))
print("h1=%d h2=%d table=%d note=%d ol=%d ul=%d riskbox=%d"
      % (h.count("<h1"), h.count("<h2"), h.count("<table"),
         h.count('class="note"'), h.count("<ol>"), h.count("<ul>"),
         h.count("riskbox")))
leak = [k for k, rx in (("/search/", r"/search/search"),
                        ("/record/", r"/record/query"),
                        ("curl", r"\bcurl\b"),
                        ("AccessToken", r"AccessToken"),
                        ("请求参数", r"pageRowBounds"),
                        ("精确条数", r"146,?020|146,?021|12139|12,139"),
                        ("字段英文名", r"identityCard|idNumber|unifiedExamination"))
        if re.search(rx, h)]
print("技术细节残留:", leak or "无")
print("占位/链接:", re.findall(r"【[^】]*】|minecraft_lhz@163\.com|feedback\.mclhz\.de5\.net", h))