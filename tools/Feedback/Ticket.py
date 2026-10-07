"""反馈工单模板 —— 造 HTML 工单 + 投递前脱敏闸门（纯函数，无网络，可单测）。

对应：给 `SendFeedback.py` 调用；也可单独 import 复用。

三个职责：
  1. `mask_student_no()`  学号脱敏（保留前4 + 后2）
  2. `buildTicket()`    拼 HTML 工单（自报错型/未覆盖型/安全型）
  3. `scan()`           投递前敏感信息闸门，命中即拦下
"""
import html
import re

# ---- 脱敏闸门：命中即拒投。宁可误报也不能把凭据/隐私寄出去。
# email 不在闸门里——它是被允许的字段（Reply-To）；正文里的邮箱由调用方自觉。
GATES = [
    ("ssoToken/记录id(32位hex)", re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])")),
    ("JSESSIONID", re.compile(r"JSESSIONID", re.I)),
    ("Authorization头", re.compile(r"Authorization", re.I)),
    ("口令字段", re.compile(r"(?:password|passwd|密码|口令)\s*[:=]", re.I)),
    ("身份证号(18位)", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("护照/证件号", re.compile(r"(?<![0-9A-Za-z])[A-Z]\d{8,}[0-9A-Z]")),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("学号未脱敏(11位)", re.compile(r"(?<!\d)\d{11}(?!\d)")),
    # 以下三条是 2026-10-06 补的：闸门只挡凭据与证件是不够的，工单正文一旦粘进
    # 一段接口返回，就会连着别人的姓名、班级、userId 一起发到第三方服务。
    ("userId", re.compile(r"userId\s*[:=]\s*\d{4,}")),
    ("班级(如 8班)", re.compile(r"(?<!\d)\d{1,2}\s*班")),
    ("姓名字段", re.compile(r"(?:姓名|学生|本人)\s*[:：=]\s*[一-龥]{2,4}")),
]

KIND_LABEL = {"bug": "报错", "gap": "功能未覆盖", "security": "安全问题"}


def mask_student_no(sid, head=4, tail=2):
    """学号脱敏：保留前 4 + 后 2，中间全部 `*`。纯数字不足 head+tail 则全打码。"""
    s = re.sub(r"\D", "", str(sid or ""))
    if not s:
        return ""
    if len(s) <= head + tail:
        return "*" * len(s)
    return s[:head] + "*" * (len(s) - head - tail) + s[-tail:]


def scan(payload_text):
    """扫描文本，返回命中列表 [(标签, 片段, 偏移)]。空列表=可投。"""
    hits = []
    for label, rx in GATES:
        for m in rx.finditer(payload_text):
            frag = m.group(0)
            shown = frag[:6] + "…" + frag[-2:] if len(frag) > 10 else frag
            hits.append((label, shown, max(0, m.start() - 24)))
    return hits


def _kv(rows):
    out = ['<table style="border-collapse:collapse;width:100%;margin:0 0 14px">']
    for k, v in rows:
        out.append(
            '<tr>'
            '<td style="padding:5px 12px 5px 0;color:#666;white-space:nowrap;'
            'vertical-align:top;border-bottom:1px solid #eee">%s</td>'
            '<td style="padding:5px 0;border-bottom:1px solid #eee">%s</td>'
            "</tr>" % (html.escape(str(k)), v))
    out.append("</table>")
    return "".join(out)


def _sec(title, body_html):
    return ('<div style="margin:14px 0 6px;font-weight:600;color:#111">%s</div>%s'
            % (html.escape(str(title)), body_html))


def _pre(text):
    return ('<pre style="margin:0;white-space:pre-wrap;font-family:Consolas,'
            'Menlo,monospace;font-size:12px">%s</pre>' % html.escape(str(text)))


def build_ticket(kind, title, name, sid, sections, repro, impact, found="2026-10-05"):
    """拼一张 HTML 工单。

    kind     bug / gap / security
    sections [(小节标题, 正文), ...]  正文按纯文本渲染并 escape
    repro    复现步骤（纯文本）
    impact   影响面（纯文本）
    """
    parts = [_kv([
        ("问题类型", html.escape(KIND_LABEL.get(kind, kind))),
        ("标题", html.escape(title)),
        ("提交人", html.escape(name or "Anonymous")),
        ("学号（脱敏）", "<code>%s</code>" % html.escape(mask_student_no(sid))),
        ("发现时间", html.escape(found)),
    ])]
    for t, b in (sections or []):
        parts.append(_sec(t, _pre(b)))
    parts.append(_sec("复现步骤（脱敏）", _pre(repro)))
    parts.append(_sec("影响面", _pre(impact)))
    return ('<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,'
            'Arial,sans-serif;font-size:14px;color:#111">%s</div>'
            % "".join(parts))