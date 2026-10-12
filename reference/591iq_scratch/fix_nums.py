"""修正 sync_article.py 的小节编号：新机制插在原第6节之后，故应为 7/8，其后各 +2。"""
import io
import os

P = os.path.join(os.environ["TEMP"], "591iq_scratch", "sync_article.py")
t = io.open(P, encoding="utf-8").read()

# 1) 新增两节的编号 6/7 -> 7/8
t = t.replace('<div class="n">6</div><h2>机制六 · 能力边界</h2>',
              '<div class="n">7</div><h2>机制六 · 能力边界</h2>')
t = t.replace('<div class="n">7</div><h2>机制七 · 可观测与安全上报</h2>',
              '<div class="n">8</div><h2>机制七 · 可观测与安全上报</h2>')
t = t.replace("<!-- 6 新增 机制六：能力边界 -->", "<!-- 7 新增 机制六：能力边界 -->")
t = t.replace("<!-- 7 新增 机制七：可观测与上报 -->", "<!-- 8 新增 机制七：可观测与上报 -->")

# 2) 原有 7/8/9/10 顺延为 9/10/11/12（先改注释锚点，再改可见编号）
for old, new in (('<!-- 7 文档层制度 -->', '<!-- 9 文档层制度 -->'),
                 ('<!-- 8 代码层实现对照 -->', '<!-- 10 代码层实现对照 -->'),
                 ('<!-- 9 已知缺口 -->', '<!-- 11 已知缺口 -->'),
                 ('<!-- 10 结论 -->', '<!-- 12 结论 -->')):
    assert old in t, old
    t = t.replace(old, new)

for old, new in (("'<div class=\"n\">7</div><h2>文档层制度</h2>', '<div class=\"n\">8</div>",
                  "'<div class=\"n\">7</div><h2>文档层制度</h2>', '<div class=\"n\">9</div>"),
                 ("'<div class=\"n\">8</div><h2>代码层实现对照</h2>', '<div class=\"n\">9</div>",
                  "'<div class=\"n\">8</div><h2>代码层实现对照</h2>', '<div class=\"n\">10</div>"),
                 ("'<div class=\"n\">9</div><h2>已知缺口（如实标注）</h2>', '<div class=\"n\">10</div>",
                  "'<div class=\"n\">9</div><h2>已知缺口（如实标注）</h2>', '<div class=\"n\">11</div>"),
                 ("'<div class=\"n\">10</div><h2>设计结论</h2>', '<div class=\"n\">11</div>",
                  "'<div class=\"n\">10</div><h2>设计结论</h2>', '<div class=\"n\">12</div>")):
    assert old in t, old[:50]
    t = t.replace(old, new)

# 3) 插入锚点必须落在原第8节注释（新编号）上
t = t.replace("anchor = '  <!-- 7 文档层制度 -->'",
              "anchor = '  <!-- 9 文档层制度 -->'")

io.open(P, "w", encoding="utf-8", newline="").write(t)
print("脚本已修正")