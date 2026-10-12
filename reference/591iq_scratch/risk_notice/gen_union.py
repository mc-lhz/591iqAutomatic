"""学生会版 Markdown → 可打印 HTML（复用正式版的渲染器与样式）。"""
import io
import os
import subprocess
import sys

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
MD = os.path.join(D, "风险说明-学生会版.md")
HTML = os.path.join(D, "风险说明-学生会版.html")

# 复用 md2html.py 的渲染逻辑，但换输入输出与标题
src = io.open(os.path.join(D, "md2html.py"), encoding="utf-8").read()
src = src.replace('src = os.path.join(D, "风险通知单.md")',
                  'src = os.path.join(D, "风险说明-学生会版.md")')
src = src.replace('dst = os.path.join(D, "风险通知单.html")',
                  'dst = os.path.join(D, "风险说明-学生会版.html")')
src = src.replace("<title>关于新壹我（天蛙）综合素质评价系统两处检索接口越权风险的通知单</title>",
                  "<title>关于新壹我系统中两处越权访问问题的说明（学生会版）</title>")
src = src.replace("编号 RISK-2026-1006-01 · 2026-10-06 · 请勿外传。",
                  "编号 RISK-2026-1006-01（学生会版） · 2026-10-06 · 本件不含技术细节。")

tmp = os.path.join(D, "_gen.py")
io.open(tmp, "w", encoding="utf-8", newline="").write(src)
r = subprocess.run([sys.executable, "-X", "utf8", tmp], capture_output=True,
                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
sys.stdout.write(r.stdout.decode("utf-8", "replace"))
sys.stderr.write(r.stderr.decode("utf-8", "replace"))
os.remove(tmp)

h = io.open(HTML, encoding="utf-8").read()
print("--- 学生会版体检 ---")
import re
bad = [k for k, rx in (
    ("接口路径 /search/", r"/search/search"),
    ("接口路径 /record/", r"/record/query"),
    ("curl 复现命令", r"\bcurl\b"),
    ("AccessToken 字段", r"AccessToken"),
    ("请求参数 JSON", r'pageRowBounds|\"type\"\s*:'),
    ("精确条数 146020", r"146,?020"),
    ("精确条数 2324", r"2324"),
    ("字段名 identityCard 等", r"identityCard|idNumber|unifiedExamination"),
) if re.search(rx, h)]
print("命中敏感项:", bad or "无")