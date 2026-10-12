"""从全量测试日志里统计各端点的响应信封形状，枚举 {meta:{code,msg}} 型端点。"""
import os
import re
import sys
from collections import Counter

D = os.path.join(os.environ["TEMP"], "591iq_scratch", "logs")
LINE = re.compile(r"<- (\S+) (\S+) (\d+)ms code=(\S+) 信封=\[(.*)\]\s*$")

rows = []
for name in ("readonly.log", "recordread.log", "contract.log"):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        continue
    for raw in open(p, encoding="utf-8", errors="replace"):
        m = LINE.search(raw.strip())
        if m:
            rows.append((m.group(1), m.group(4), m.group(5)))

print("解析到响应行:", len(rows))
meta_paths, code_paths = Counter(), Counter()
for path, code, env in rows:
    keys = [k.strip().strip("'") for k in env.split(",") if k.strip()]
    (meta_paths if ("meta" in keys and "code" not in keys) else code_paths)[path] += 1

print("\n=== meta 信封（顶层无 code，D17 的受害者；旧实现会把它们的失败当成功）===")
for p, n in sorted(meta_paths.items()):
    print("  %-44s %d 次" % (p, n))
print("  小计 %d 个端点" % len(meta_paths))
print("\n=== 顶层 code 信封 ===")
print("  %d 个端点（%s …）" % (len(code_paths), "、".join(sorted(code_paths)[:4])))
print("\n=== 出现过非 0 code 的端点 ===")
for path, code, env in sorted(set((p, c, e) for p, c, e in rows if c not in ("0", "None"))):
    print("  %-44s code=%s" % (path, code))
sys.exit(0 if meta_paths else 2)