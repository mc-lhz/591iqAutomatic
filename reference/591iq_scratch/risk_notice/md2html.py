"""把风险通知单（Markdown）转成可打印的独立 HTML：纯内联样式、无外部资源，A4 友好。

注意：必须处理 ``` 围栏代码块，否则请求样例会散架。
"""
import io
import os
import re

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
src = os.path.join(D, "风险通知单.md")
dst = os.path.join(D, "风险通知单.html")

md = io.open(src, encoding="utf-8").read()


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


out, i = [], 0
lines = md.split("\n")
while i < len(lines):
    ln = lines[i]

    if ln.strip().startswith("```"):                      # 围栏代码块
        lang = ln.strip()[3:].strip()
        i += 1
        buf = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            buf.append(lines[i])
            i += 1
        i += 1
        cls = ' class="lang-%s"' % re.sub(r"\W+", "", lang) if lang else ""
        out.append("<pre%s><code>%s</code></pre>"
                   % (cls, "\n".join(buf).replace("&", "&amp;")
                      .replace("<", "&lt;").replace(">", "&gt;")))
        continue

    if not ln.strip():
        i += 1
        continue

    if ln.startswith("|"):
        block = []
        while i < len(lines) and lines[i].startswith("|"):
            block.append(lines[i])
            i += 1
        rows = [split_row(b) for b in block]
        head = rows[0]
        body = [r for r in rows[1:]
                if not all(re.fullmatch(r":?-{2,}:?", (c or "-").strip()) for c in r)]
        out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
            "".join("<th>%s</th>" % inline(c) for c in head),
            "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                    for r in body)))
        continue

    m = re.match(r"^(#{1,4})\s+(.*)$", ln)
    if m:
        lv = len(m.group(1))
        out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
        i += 1
        continue

    if re.match(r"^---+$", ln.strip()):
        out.append("<hr>")
        i += 1
        continue

    if ln.startswith("> "):
        out.append("<blockquote>%s</blockquote>" % inline(ln[2:].strip()))
        i += 1
        continue

    if re.match(r"^\s*[-*]\s+(.*)$", ln):
        out.append("<li>%s" % inline(re.sub(r"^\s*[-*]\s+", "", ln)))
        i += 1
        continue

    m = re.match(r"^\s*(\d+)\.\s+(.*)$", ln)
    if m:
        out.append("<oli>%s" % inline(m.group(2)))
        i += 1
        continue

    out.append("<p>%s</p>" % inline(ln))
    i += 1

body = "\n".join(out)
# 收拢被拆散的连续列表项
body = re.sub(r"<p></p>", "", body)
body = re.sub(r"</li>\s*(?=<li>)", "", body)
body = re.sub(r"(<li>.*?</li>)\s*(?=<p|<h|<table|<pre|<blockquote|</ul>|</ol>)",
              r"\1", body, flags=re.S)
body = re.sub(r"<p>(<li>.*?)</p>", r"\1", body, flags=re.S)
body = re.sub(r"<p>\s*</li>\s*</p>", "</li>", body)


def close_list(html):
    """在列表被段落/其它块打断的地方补上闭合标签。"""
    html = re.sub(r"(<li>.*?</li>)\s*(?=<p>|<h\d|<table|<pre|<blockquote|<hr)",
                  r"\1</ul>\n", html, flags=re.S)
    html = re.sub(r"(<oli>.*?</oli>)\s*(?=<p>|<h\d|<table|<pre|<blockquote|<hr)",
                  r"\1</ol>\n", html, flags=re.S)
    return html


body = close_list(body)
body = re.sub(r"(<li>[\s\S]*?</li>)(?![\s\S]*?</li>)", r"\1</ul>", body)
body = re.sub(r"(<oli>[\s\S]*?</oli>)(?![\s\S]*?</oli>)", r"\1</ol>", body)
body = re.sub(r"</ul>\s*</ul>", "</ul>", body)
body = re.sub(r"</ol>\s*</ol>", "</ol>", body)

CSS = """
:root{--ink:#1a2332;--ink2:#4a5b70;--ink3:#7d8da8;--line:#d9e0ea;--bg:#fff;
--blue:#1d5bb8;--red:#c0392b;--warn:#b45309;--chip:#eef3fb}
*{box-sizing:border-box}
body{font:15px/1.75 "Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;color:var(--ink);
background:#eef1f5;margin:0;padding:32px 16px}
.sheet{max-width:860px;margin:0 auto;background:var(--bg);padding:52px 60px 60px;
box-shadow:0 2px 20px rgba(20,30,50,.08)}
h1{font-size:24px;line-height:1.42;margin:0 0 20px;padding-bottom:16px;
border-bottom:3px solid var(--blue);letter-spacing:-.3px}
h2{font-size:19px;margin:34px 0 12px;padding-left:11px;border-left:4px solid var(--blue)}
h3{font-size:16px;margin:22px 0 8px;color:var(--blue)}
p{margin:10px 0}
ul,ol{margin:10px 0 12px 22px;padding:0}
li{margin:5px 0}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:#f3f7fc;font-weight:600}
code{font-family:Consolas,Menlo,monospace;font-size:.88em;background:var(--chip);
color:var(--red);padding:1px 5px;border-radius:3px}
pre{background:#f6f8fb;border:1px solid var(--line);border-left:3px solid var(--blue);
padding:12px 14px;margin:12px 0;overflow-x:auto}
pre code{background:none;color:var(--ink);padding:0;font-size:12.5px;line-height:1.6;
white-space:pre}
blockquote{margin:14px 0;padding:10px 16px;background:#fffaf0;
border-left:3px solid var(--warn);color:var(--ink2)}
hr{border:none;border-top:1px solid var(--line);margin:28px 0}
strong{font-weight:700}
.foot{margin-top:36px;padding-top:16px;border-top:1px solid var(--line);
font-size:12.5px;color:var(--ink3)}
@media print{body{background:#fff;padding:0}.sheet{box-shadow:none;padding:0;max-width:none}
tr,table,pre{page-break-inside:avoid}h2,h3{page-break-after:avoid}}
"""

HTML = ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
        "<title>关于新壹我（天蛙）综合素质评价系统两处检索接口越权风险的通知单</title>\n"
        "<style>%s</style>\n</head>\n<body>\n<div class=\"sheet\">\n%s\n"
        "<div class=\"foot\">本文件为技术风险通报，不构成法律意见。"
        "编号 RISK-2026-1006-01 · 2026-10-06 · 请勿外传。</div>\n</div>\n"
        "</body>\n</html>\n") % (CSS, body)

io.open(dst, "w", encoding="utf-8", newline="").write(HTML)
print("written -> %s (%d bytes)" % (dst, len(HTML.encode("utf-8"))))