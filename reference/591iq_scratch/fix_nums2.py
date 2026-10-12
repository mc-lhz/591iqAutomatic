"""把 sync_article.py 的编号逻辑改成最简形式：

- HTML 注释不可见，不动它；
- 插入锚点用**源文件里真实存在**的 `<!-- 7 文档层制度 -->`；
- 只改「可见编号」：新增两节 = 7 / 8，原 7/8/9/10 → 9/10/11/12。
"""
import io
import os

P = os.path.join(os.environ["TEMP"], "591iq_scratch", "sync_article.py")
t = io.open(P, encoding="utf-8").read()

# 注释编号还原成源文件原样（重新生成脚本时它们本就匹配，此处确保一致）
for a, b in (('<!-- 9 文档层制度 -->', '<!-- 7 文档层制度 -->'),
             ('<!-- 10 代码层实现对照 -->', '<!-- 8 代码层实现对照 -->'),
             ('<!-- 11 已知缺口 -->', '<!-- 9 已知缺口 -->'),
             ('<!-- 12 结论 -->', '<!-- 10 结论 -->')):
    t = t.replace(a, b)

# 锚点回退
t = t.replace("anchor = '  <!-- 9 文档层制度 -->'",
              "anchor = '  <!-- 7 文档层制度 -->'")

# 删掉「章节号」注释重命名那一段（不再需要，且会与源文件不匹配）
start = t.find("# 章节号顺延")
end = t.find('sub(\'<div class="n">7</div><h2>文档层制度</h2>')
if start > 0 and end > start:
    t = t[:start] + t[end:]

# 可见编号：原 7/8/9/10 -> 9/10/11/12
for old, new in (("'<div class=\"n\">7</div><h2>文档层制度</h2>', '<div class=\"n\">9</div>",
                  "'<div class=\"n\">7</div><h2>文档层制度</h2>', '<div class=\"n\">9</div>"),
                 ("'<div class=\"n\">8</div><h2>代码层实现对照</h2>', '<div class=\"n\">10</div>",
                  "'<div class=\"n\">8</div><h2>代码层实现对照</h2>', '<div class=\"n\">10</div>"),
                 ("'<div class=\"n\">9</div><h2>已知缺口（如实标注）</h2>', '<div class=\"n\">11</div>",
                  "'<div class=\"n\">9</div><h2>已知缺口（如实标注）</h2>', '<div class=\"n\">11</div>"),
                 ("'<div class=\"n\">10</div><h2>设计结论</h2>', '<div class=\"n\">12</div>",
                  "'<div class=\"n\">10</div><h2>设计结论</h2>', '<div class=\"n\">12</div>")):
    t = t.replace(old, new)

io.open(P, "w", encoding="utf-8", newline="").write(t)
print("已修正；新增两节编号 =", "7 / 8")