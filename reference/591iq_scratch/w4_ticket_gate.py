"""W4：反馈工单外发闸门自检——粘进一段接口返回时必须拦得住。"""
import json
import os
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools"))
from Feedback.Ticket import build_ticket, scan   # noqa: E402

LEAKY_BODY = """复现步骤：
1. 调 /user/getUserInfoDetail，返回里 userId=787316，
   提交人姓名：林昊哲，班级 高二(2025级)8班
2. 附件含 ssoToken=3d4eb6d6b9d04ab18da50d2d6e567972
"""
CLEAN_BODY = """复现步骤：
1. 调 /user/getUserInfoDetail，返回里 userId=<已脱敏>，班级字段已清空
2. 请求带 AccessToken（值已删），响应 code=0
问题原因：字段层级写错，封装层吞掉了参数。
"""


def run(label, body):
    html_body = build_ticket("bug", "标题", "", "", [("问题描述", body)],
                             "（见问题描述）", "（见问题描述）")
    blob = json.dumps({"message": html_body, "name": "", "email": ""},
                      ensure_ascii=False)
    hits = scan(blob)
    print("%-8s %-6s 命中 %d 处：%s"
          % (label, "拦下" if hits else "放行", len(hits),
             "、".join(sorted({h[0] for h in hits}))))
    return len(hits)


a = run("含PII", LEAKY_BODY)
b = run("已脱敏", CLEAN_BODY)
print("\n结论:", "PASS" if a >= 4 and b == 0 else
      "FAIL 含PII 命中 %d（期望≥4）/ 脱敏版命中 %d（期望 0）" % (a, b))
sys.exit(0 if (a >= 4 and b == 0) else 1)