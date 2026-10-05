"""反馈工单 CLI —— 发现报错/功能未覆盖时，填工单投给 feedback.mclhz.de5.net。

用法：
  # 先预览（不发送、不落盘）
  python tools/Feedback/SendFeedback.py --type gap --title "..." --detail 问题.md --dry-run
  # 确认后真发
  python tools/Feedback/SendFeedback.py --type gap --title "..." --detail 问题.md --yes

设计约束：
  · --detail 传纯文本/Markdown 文件，作为工单正文；也可用--message 直接传串。
  · 姓名(--name)与学号(--sid)进工单头部，学号强制脱敏(mask_student_no)。
  · 投递前过脱敏闸门(scan)，命中token/证件/手机号/未脱敏学号即拒发。
  · 写入类操作必须显式 --yes（沿用 PublishActivity/DeleteRecord 契约）。

退出码：0 成功 / 2 服务端 4xx 拒收 / 3 429 配额 / 4 网络错/ 5 脱敏闸门拦下 / 6 本地校验失败
"""
import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Feedback.FeedbackClient import post_feedback            # noqa: E402
from Feedback.Ticket import build_ticket, scan                # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="提交反馈工单（--dry-run 预览 / --yes 真发）")
    ap.add_argument("--type", choices=("bug", "gap", "security"), default="bug",
                    help="问题类型：bug报错 / gap功能未覆盖 / security安全问题")
    ap.add_argument("--title", required=True, help="一句话标题")
    ap.add_argument("--message", default="", help="正文（直接传串）")
    ap.add_argument("--detail", default="", help="正文文件路径（--message 优先）")
    ap.add_argument("--name", default="", help="提交人姓名（留空→Anonymous）")
    ap.add_argument("--sid", default="", help="学号（仅用于脱敏后展示，不传原值）")
    ap.add_argument("--email", default="", help="回信邮箱（可选，填了作Reply-To）")
    ap.add_argument("--page", default="", help="来源页/模块（可选）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 payload，不发送")
    ap.add_argument("--yes", action="store_true", help="确认发送")
    a = ap.parse_args()

    # 组装正文
    if a.message:
        body = a.message
    elif a.detail:
        if not os.path.exists(a.detail):
            print("找不到正文文件：%s" % a.detail, file=sys.stderr)
            return 6
        body = io.open(a.detail, encoding="utf-8").read()
    else:
        body = ""
    if not body.strip():
        print("正文为空：给--message 或 --detail", file=sys.stderr)
        return 6

    # 工单正文（HTML），复现/影响从正文里不强行解析——整体当detail 展示
    html_body = build_ticket(
        kind=a.type, title=a.title, name=a.name, sid=a.sid,
        sections=[("问题描述", body)], repro="（见问题描述）",
        impact="（见问题描述）")

    payload = {"message": html_body, "name": a.name, "email": a.email,
               "page": a.page}

    # 脱敏闸门：扫整个 payload
    blob = json.dumps(payload, ensure_ascii=False)
    hits = scan(blob)
    print("脱敏闸门：%s" % ("未命中，可投" if not hits else "命中 %d 处，已拦下" % len(hits)))
    for label, frag, at in hits:
        print("  [%s] %s … (偏移 %d)" % (label, frag, at))
    if hits:
        print("\n=== 工单正文（未发送）===\n%s" % html_body)
        return 5

    if a.dry_run:
        print("\n=== 投递 payload（%d 字符 / %d 字节）===\n%s"
              % (len(blob), len(blob.encode("utf-8")), html_body))
        return 0
    if not a.yes:
        print("未指定 --dry-run / --yes，不做任何事")
        return 6

    status, out = post_feedback(**payload)
    print("\nHTTP %s -> %s" % (status, json.dumps(out, ensure_ascii=False)))
    if status == 200 and out.get("ok"):
        print("反馈已受理 id=%s" % out.get("id"))
        return 0
    if status == 429:
        print("发送过于频繁/配额超限，请稍后再试", file=sys.stderr)
        return 3
    if 400 <= status < 500:
        print("服务端拒收：%s" % out.get("error"), file=sys.stderr)
        return 2
    print("邮件发送失败或网络异常", file=sys.stderr)
    return 4


if __name__ == "__main__":
    sys.exit(main())