"""端点覆盖审计：bundle 端点清单 vs skill 封装集，输出同族缺口报告（只读）。

背景：2026-10-25「点赞漏检」复盘——`/record/favour` 与 `/record/comment` 同处
记录卡片 chunk 家族，但当时的闭包分析没圈到、建模块时又只取了评论四口，
同 chunk 的 favour/collect 就此隐身。本工具把这类盲区变成**可复跑检查**：
凡某段已有端点被封装、却仍有未覆盖的同段端点，逐条列出（同族缺口）。

输入：
- `--inventory`：bundle 静态扫描产物（`{"<路径>": [chunk 文件…]}`）。
  默认取本地分析目录 `%TEMP%` 下的 591iq_scratch frontend-js 产物（不入库）。
- `--routes`：可选，路由清单（`[[path, chunks], …]`），用于剔除前端路由噪声。
  默认同名目录下的 `all_routes.json`（存在才用）。
- 封装集：**实时扫描仓库** `tools/` 下所有 .py 的 `"/xxx/yyy"` 路径字面量。

用法：
    python tools/TestCases/ApiCoverageAudit.py
    python tools/TestCases/ApiCoverageAudit.py --segment record      # 只看某段
    python tools/TestCases/ApiCoverageAudit.py --out diff.json       # 完整差集落盘
    python tools/TestCases/ApiCoverageAudit.py --inventory <自己抓的清单.json>

退出码：0 审计完成 / 2 缺清单文件（提示先按 reference/api.md 优先级链第 5 步重抓）。
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(_HERE)
ROOT = os.path.dirname(TOOLS)

DEFAULT_DIR = os.path.join(os.environ.get("TEMP", os.getcwd()),
                           "591iq_scratch", "frontend-js-20261024")

PATH_RE = re.compile(r'"(/[A-Za-z][A-Za-z0-9_]*(?:/[A-Za-z0-9_]+)+)"')


def wrappedEndpoints():
    """扫仓库 tools/ 全部 .py 的路径字面量 → 已封装端点集。"""
    out = set()
    for dp, _dn, fns in os.walk(TOOLS):
        if "__pycache__" in dp:
            continue
        for fn in fns:
            if fn.endswith(".py"):
                s = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
                out |= set(PATH_RE.findall(s))
    return out


def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="端点覆盖审计：清单（bundle 扫描产物）vs 封装集（tools/ 实时扫描），"
                    "重点输出「同族缺口」——该段已有封装却仍有未覆盖的兄弟端点。")
    ap.add_argument("--inventory", default=os.path.join(DEFAULT_DIR, "api_inventory.json"))
    ap.add_argument("--routes", default=os.path.join(DEFAULT_DIR, "all_routes.json"))
    ap.add_argument("--segment", default="", help="只审计某个首段（如 record / evaluateActivity）")
    ap.add_argument("--out", default="", help="完整差集落盘为 JSON")
    a = ap.parse_args()

    if not os.path.exists(a.inventory):
        print("[audit] 找不到清单文件：%s" % a.inventory, file=sys.stderr)
        print("[audit] 先按 reference/api.md「未知槽位结构怎么查」第 5 步抓一次前端 bundle，"
              "或直接传 --inventory <路径>", file=sys.stderr)
        return 2
    inv = json.load(open(a.inventory, encoding="utf-8"))
    routes = set()
    if a.routes and os.path.exists(a.routes):
        for row in json.load(open(a.routes, encoding="utf-8")):
            if isinstance(row, (list, tuple)) and row:
                routes.add(row[0])

    wrapped = wrappedEndpoints()
    all_eps = set(inv)
    uncovered = sorted(all_eps - wrapped - routes)
    covered = sorted(all_eps & wrapped)

    seg_of = lambda p: p.split("/")[1] if p.count("/") >= 2 else p
    covered_segs = {seg_of(p) for p in covered}
    by_seg = {}
    for p in uncovered:
        by_seg.setdefault(seg_of(p), []).append(p)

    if a.segment:
        by_seg = {k: v for k, v in by_seg.items() if k == a.segment}

    print("[audit] 清单端点 %d | 已封装（含仓库字面量）%d | 未覆盖 %d | 路由噪声剔除 %d"
          % (len(all_eps), len(covered), len(uncovered), len(all_eps & routes)))
    print()
    print("=== 同族缺口（该段已有封装，仍有未覆盖；按未覆盖数降序）===")
    siblings = {k: sorted(v) for k, v in by_seg.items() if k in covered_segs}
    for seg in sorted(siblings, key=lambda k: -len(siblings[k])):
        ps = siblings[seg]
        print("  [%s] 未覆盖 %d 条：" % (seg, len(ps)))
        for p in ps[:12]:
            print("      %s  (%d chunks)" % (p, len(inv[p])))
        if len(ps) > 12:
            print("      …（共 %d，其余见 --out）" % len(ps))
    print()
    print("=== 整段未覆盖（该段尚无任何封装；教师/管理端居多）===")
    fresh = {k: sorted(v) for k, v in by_seg.items() if k not in covered_segs}
    for seg in sorted(fresh, key=lambda k: -len(fresh[k]))[:15]:
        print("  [%-22s] %d 条" % (seg, len(fresh[seg])))

    if a.out:
        json.dump({"uncovered": uncovered, "by_segment": by_seg,
                   "wrapped": covered}, open(a.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n[audit] 差集已落盘：%s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())