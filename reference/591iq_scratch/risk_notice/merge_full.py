"""生成 Full Version：正式通知单正文 + 附件 A 合并为一份自包含文档。

标题层级：正文 `#`(标题) / `##`(一~七) / `###`(问题一)；附件降级为 `##`(附件A) / `###`(A.1~A.6)。
"""
import io
import os
import re

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "risk_notice")
main = io.open(os.path.join(D, "风险通知单.md"), encoding="utf-8").read()
att = io.open(os.path.join(D, "附件A-接口与实测数据摘要.md"), encoding="utf-8").read()

# --- 附件：去掉自己的标题与元信息表，标题降级（跳过围栏代码块内的 # 注释行） ---
att_lines = att.split("\n")
out_att, in_fence = [], False
for ln in att_lines:
    if ln.lstrip().startswith("```"):
        in_fence = not in_fence
        out_att.append(ln)
        continue
    if in_fence:
        out_att.append(ln)
        continue
    if ln.startswith("# "):
        out_att.append("## 附件 A · 两处接口的调用参数与实测数据摘要")
        continue
    if ln.startswith("**编号**") or ln.startswith("**日期**"):
        continue
    if ln.startswith("### "):
        out_att.append("#### " + ln[4:].lstrip("# "))
        continue
    if ln.startswith("## "):
        out_att.append("### " + ln[3:].lstrip("# "))
        continue
    out_att.append(ln)
att_body = "\n".join(out_att).strip()

# --- 正文：把「随附材料」那段换成全文包含说明 ---
main = main.replace(
    "| **主题** | 两个检索接口在学生角色下可返回超出界面设计的范围与敏感度 |",
    "| **主题** | 两个检索接口在学生角色下可返回超出界面设计的范围与敏感度 |\n"
    "| **版本** | **完整版（正文 + 附件 A 合订）** |")

old_tail = """## 随附材料

- **附件 A**：《两处接口的调用参数与实测数据摘要》

---"""
new_tail = """## 随附材料

- **附件 A**：《两处接口的调用参数与实测数据摘要》 —— **已合订于本文档下半部分**，无需另附。

---"""
if old_tail in main:
    main = main.replace(old_tail, new_tail)
    print("OK   随附材料段已改写")
else:
    print("MISS 随附材料段（保持原样也可）")

full = main.rstrip() + "\n\n---\n\n" + att_body + "\n"

dst = os.path.join(D, "风险通知单-Full.md")
io.open(dst, "w", encoding="utf-8", newline="").write(full)
print("written -> %s (%d 字符)" % (dst, len(full)))

# 自检：标题层级（跳过围栏代码块）+ 关键断言
def headings(md):
    hs, fence = [], False
    for ln in md.split("\n"):
        if ln.lstrip().startswith("```"):
            fence = not fence
        elif not fence and ln.startswith("#"):
            hs.append(ln)
    return hs


hs = headings(full)
h1 = [x for x in hs if x.startswith("# ")]
h2 = [x for x in hs if x.startswith("## ")]
print("H1=%d H2=%d H3=%d" % (len(h1), len(h2), len([x for x in hs if x.startswith("### ")])))
print("H1 标题:", h1[0] if h1 else "（无）")
print("H2 列表:", " / ".join(x[3:].strip() for x in h2))
assert len([x for x in h2 if x.startswith("## 附件 A")]) == 1, "附件标题重复"
assert len(h1) == 1, "H1 不唯一"
assert "### A.6" in full and "#### " not in full, "A.6 层级异常"
print("OK   附件标题唯一、H1 唯一、A.1~A.6 层级正确")
print("待填占位:", re.findall(r"【[^】]*】", full))