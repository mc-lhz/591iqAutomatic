"""Full Version Markdown → 可打印 HTML（复用正式版渲染器与样式）。"""
import io
import os
import re
import subprocess
import sys

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
MD = os.path.join(D, "风险通知单-Full.md")
HTML = os.path.join(D, "风险通知单-Full.html")

src = io.open(os.path.join(D, "md2html.py"), encoding="utf-8").read()
src = src.replace('src = os.path.join(D, "风险通知单.md")',
                  'src = os.path.join(D, "风险通知单-Full.md")')
src = src.replace('dst = os.path.join(D, "风险通知单.html")',
                  'dst = os.path.join(D, "风险通知单-Full.html")')
src = src.replace("<title>关于新壹我（天蛙）综合素质评价系统两处检索接口越权风险的通知单</title>",
                  "<title>关于新壹我（天蛙）综合素质评价系统两处检索接口越权风险的通知单（完整版）</title>")

tmp = os.path.join(D, "_gen_full.py")
io.open(tmp, "w", encoding="utf-8", newline="").write(src)
r = subprocess.run([sys.executable, "-X", "utf8", tmp], capture_output=True,
                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
sys.stdout.write(r.stdout.decode("utf-8", "replace"))
sys.stderr.write(r.stderr.decode("utf-8", "replace"))
os.remove(tmp)

h = io.open(HTML, encoding="utf-8").read()
print("--- Full 版体检 ---")
checks = [
    ("无外部外链（可离线/打印）", not re.search(r'(?:href|src)="https?://', h)),
    ("代码块未崩（<pre> 存在）", "<pre" in h),
    ("表格已渲染（<table> 存在）", "<table" in h),
    ("附件 A 已内联（A.6 小节）", "A.6" in h),
    ("标题含「完整版」", "完整版" in h),
    ("含 noindex", "noindex" in h),
    ("精确条数 146,020 在正文/附件", "146,020" in h or "146020" in h),
    ("含 curl 复现（正式版应有）", bool(re.search(r"\bcurl\b", h))),
    ("仅剩一个 <h1>", h.count("<h1") == 1),
]
for k, v in checks:
    print(("  [OK] " if v else "  [!!] ") + k)
print("字节数 %d，h2=%d，表格=%d，代码块=%d"
      % (len(h.encode("utf-8")), h.count("<h2"), h.count("<table"), h.count("<pre")))
print("待填占位:", re.findall(r"【[^】]*】", h))
