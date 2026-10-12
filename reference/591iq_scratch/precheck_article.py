"""发布前体检：确认 article_new.html 可公开（无 PII / 无凭据 / 无端点载荷）。"""
import io
import os
import re

P = os.path.join(os.environ["TEMP"], "591iq_scratch", "article_new.html")
h = io.open(P, encoding="utf-8").read()
print("字符数 %d / 字节 %d" % (len(h), len(h.encode("utf-8"))))

CHECKS = [
    ("32位hex(token/recordId)", r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])"),
    ("身份证18位", r"(?<!\d)\d{17}[\dXx](?!\d)"),
    ("手机号", r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    ("学号11位", r"(?<!\d)\d{11}(?!\d)"),
    ("真实fs图片地址", r"fs\.591iq\.cn/group1/\S+"),
    ("投票端点/载荷", r"commitBatchVote|deleteVoteStuff|reportConfirm|subjectHonorStuff"),
    ("越权端点路径", r"apps/credit|list_school"),
    ("真实姓名值", r"(?:studentName|userName|personName)\W{0,3}[:=]\W{0,3}[\"'][^\"']{2,4}[\"']"),
    ("门户/学号域名", r"xmyz\.xmedu"),
    ("外部可点外链", r'href="https?://(?!mc-lhz|www\.591iq)'),
]

bad = 0
for label, rx in CHECKS:
    hits = re.findall(rx, h)
    if hits:
        bad += 1
    print("  %-22s %-3d %s" % (label, len(hits),
                                 ("<<< " + str(sorted(set(hits))[:2])) if hits else ""))

print()
print("结论:", "可公开" if bad == 0 else "有 %d 项需处理" % bad)