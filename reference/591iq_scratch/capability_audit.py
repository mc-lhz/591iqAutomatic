"""能力面审计：找出「工具能做、但学生端前端没有 UI」的路径。

纯读，不发任何请求。判据来源是仓库里已固化的实测结论（api.md / MEMORY.md），
不是猜测。每条都标出证据出处与合规判断。
"""
import io
import os
import re

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
FILES = {
    "api.md": os.path.join(ROOT, "reference", "api.md"),
    "frontend.md": os.path.join(ROOT, "reference", "frontend.md"),
    "MEMORY.md": os.path.join(ROOT, "MEMORY.md"),
}

# 关键词 -> (能力描述, 判读)
PROBES = [
    (r"兜底分支", "记录列表 type 传非枚举值 → 绕过 tab 过滤，返回 146,018 条"),
    (r"146,0\d\d", "同一兜底分支的具体条数量级"),
    (r"signData|generate\(\)", "签名参数依赖前端私钥，仓库内无法生成"),
    (r"未开通", "学校未开通的 10 类记录：提交无验证信号"),
    (r"delSummary", "delSummary 在 bundle 里存在，学生端是否暴露未验证"),
    (r"reviewDel", "reviewDel 同族端点，角色归属未验证"),
    (r"list_school|学分", "教师端名册端点，学生 token 可读"),
    (r"msgauth|/account/logout", "logout 被只读正则误收，真正注销会话"),
    (r"copy|move", "copy/move 类端点语义不是只读"),
    (r"schId", "客户端 schId 参数：部分配置端点只校验类型不取值"),
    (r"listTemplate|integralAppraisalScheme|scheme/confirm", "6 处 schId 真正进请求的端点"),
    (r"session.*query|URL query", "凭据走 URL query 的导出端点"),
    (r"图片 URL 复用|复用他人", "复用他人 fs 图片 URL 是否触发 999999 未证实"),
    (r"班级评价", "班级评价前端有代码但账号全 404"),
    (r"upload", "announcement/upload 需 --upload 才计入的自测项"),
]

for label, path in FILES.items():
    text = io.open(path, encoding="utf-8").read()
    lines = text.split("\n")
    print("\n===== %s（%d 行）=====" % (label, len(lines)))
    for pat, desc in PROBES:
        rx = re.compile(pat)
        hits = [(i + 1, ln.strip()) for i, ln in enumerate(lines) if rx.search(ln)]
        if not hits:
            continue
        print("\n▸ %s" % desc)
        for n, ln in hits[:3]:
            plain = re.sub(r"[^\x20-\x7e\u4e00-\u9fff]", " ", ln)
            print("   %s:%d %s" % (label, n, plain[:104]))