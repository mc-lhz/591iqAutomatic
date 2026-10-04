"""仓库契约与卫生审计：**离线**、无网络、无凭据，CI 与本地共用同一份实现。

存在的理由：仓库的硬约束全写在 AGENTS.md 里（脱敏、reference/ 100KB 上限、命名契约、
每 py 配同名 md），但**没有任何自动化守着**，全靠人记。2026-10-04 就因为在 PowerShell
here-string 里写反引号，弄出 5 处代码标记损坏 + 一处 TAB 混入——这类事故本该被机器拦住。

用法：
    python tools/TestCases/TestContract.py            # 人类可读报告
    python tools/TestCases/TestContract.py --quiet    # 只输出汇总行（CI 用）

退出码：0 全部通过（WARN 不影响）/ 1 有 FAIL。
与 TestApiReadOnly / TestRecordRead 的区别：那两个要 token、只读线上接口；
本脚本只读本地文件与 git 元数据，**不碰网络**。
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # tools/TestCases
TOOLS = os.path.dirname(HERE)                              # tools
ROOT = os.path.dirname(TOOLS)                              # 仓库根
sys.path.insert(0, TOOLS)

OK, WARN, FAIL = "PASS", "WARN", "FAIL"
RESULTS = []

# AGENTS.md 写死的硬约束
REFERENCE_BUDGET = 100 * 1024

# 必须带 main() + __main__ 的命令行入口（其余是库模块）
CLI_ENTRIES = [
    "Access/LoginToken.py", "Access/VisionLogin.py",
    "Export/ExportXlsx.py", "Export/ExportSummaryList.py",
    "RecordCenter/PublishActivity.py", "RecordCenter/DeleteRecord.py",
    "TestCases/TestApiReadOnly.py", "TestCases/TestRecordRead.py",
    "TestCases/TestContract.py",
]
# 门面与最小库，AGENTS 的「每 py 配同名 md」在这几处历史上没做，先记 WARN 不阻断 CI
MD_EXEMPT = {"IqClient.py", "XlsxWriter.py"}

# 敏感串：只写通用形态，**绝不把真实凭据写进仓库**（否则扫描器自己就泄密）
# 乱码残留特征：**必须用码点构造**。第一版把乱码样本当字面量写在源码里，
# 结果扫描器把自己判成乱码，CI 两个平台一起红——这类「检测器自指」坑过一次就记住。
MOJIBAKE = [
    chr(0x951F) + chr(0x65A4) + chr(0x62F7),   # GBK 误解码 UTF-8 的典型产物
    chr(0xFFFD),                               # 解码失败的替换符
    chr(0xEF) + chr(0xBF) + chr(0xBD),         # U+FFFD 被按 latin-1 二次显示
]

SENSITIVE = [
    ("32 位 hex（token / recordId）", r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])"),
    ("手机号", r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    ("真实图片地址", r"fs\.591iq\.cn/group1/[A-Za-z0-9]{16,}"),
    ("硬编码密码", r"(?:password|密码|passwd)\s*[:=]\s*[\"'][^\"']{6,}[\"']"),
]
SCAN_EXT = (".py", ".md", ".json", ".jsonc", ".yml", ".yaml", ".txt")
SKIP_DIR = {".git", "__pycache__", ".github"}


def add(name, status, note=""):
    RESULTS.append((name, status, note))


def repoFiles():
    """git 跟踪的文件；不在 git 仓库里时退化成走目录树。"""
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files"],
                             capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            return [f for f in out.stdout.split("\n") if f.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    got = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            got.append(os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"))
    return got


def checkNaming(files):
    """命名契约：**tools/ 下的**目录大驼峰、模块大驼峰、无下划线/短横线、不撞标准库。

    只约束 tools/：那是业务域目录（AGENTS.md「tools/ 按业务域分目录」）；
    仓库根的 `reference/` 是文档目录，不适用大驼峰。
    """
    bad = []
    for rel in files:
        parts = rel.split("/")
        dirs, mods = parts[:-1], parts[-1]
        if not parts[0] == "tools":
            continue                      # 只管 tools/ 子树
        for d in dirs[1:]:                # 跳过 tools/ 自身
            if d in SKIP_DIR or d.endswith(".egg-info"):
                continue
            if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", d):
                bad.append("%s: 目录 %s 非大驼峰" % (rel, d))
        if rel.endswith(".py"):
            m = mods[:-3]
            if m != "__init__" and not re.fullmatch(r"[A-Z][A-Za-z0-9]*", m):
                bad.append("%s: 模块 %s 非大驼峰" % (rel, m))
            stem = os.path.splitext(mods)[0]
            if stem in ("json", "types", "code", "profile", "time", "random"):
                bad.append("%s: 模块名与标准库同名" % rel)
    add("命名契约（tools/ 大驼峰·不撞标准库）", FAIL if bad else OK,
        "；".join(bad[:3]) or "%d 个文件全部合规" % len(files))

    missing = []
    for rel in files:
        if not rel.endswith(".py") or os.path.basename(rel) == "__init__.py":
            continue
        stem = rel[:-3]
        if not os.path.exists(os.path.join(ROOT, stem + ".md")):
            missing.append(os.path.basename(rel))
    if missing:
        exempt = [m for m in missing if m in MD_EXEMPT]
        hard = [m for m in missing if m not in MD_EXEMPT]
        note = ("、".join(hard) if hard else "无（仅豁免项缺失）")
        if exempt:
            note += "；豁免：%s" % "、".join(exempt)
        add("每个 py 配同名 .md", FAIL if hard else WARN, note)
    else:
        add("每个 py 配同名 .md", OK, "全部配套齐全")


def checkSensitive(files):
    hits = []
    for rel in files:
        if not rel.lower().endswith(SCAN_EXT):
            continue
        p = os.path.join(ROOT, *rel.split("/"))
        try:
            text = io.open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            hits.append("%s: 不是合法 UTF-8" % rel)
            continue
        for label, pat in SENSITIVE:
            for m in sorted(set(re.findall(pat, text)))[:3]:
                hits.append("%s: %s → %s" % (rel, label, m))
    add("敏感串（提交前脱敏）", FAIL if hits else OK,
        "；".join(hits[:3]) or "未发现 token/手机号/密码/真实图片地址")


def checkReferenceBudget():
    refDir = os.path.join(ROOT, "reference")
    files = sorted(os.listdir(refDir)) if os.path.isdir(refDir) else []
    total = sum(os.path.getsize(os.path.join(refDir, f)) for f in files
                if os.path.isfile(os.path.join(refDir, f)))
    ok = total <= REFERENCE_BUDGET
    add("reference/ 体积预算 ≤ 100KB", OK if ok else FAIL,
        "%d KB / 100 KB（%s）" % (total // 1024, "、".join(files)))


def checkHygiene(files):
    """UTF-8 卫生：无 BOM、无 TAB、无乱码残留——2026-10-04 的反引号/TAB 事故就靠这条拦。"""
    bom, tab, mojibake = [], [], []
    for rel in files:
        if not rel.lower().endswith(SCAN_EXT):
            continue
        p = os.path.join(ROOT, *rel.split("/"))
        raw = open(p, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"):
            bom.append(rel)
        if b"\t" in raw:
            tab.append(rel)
        for token in MOJIBAKE:
            if token in raw.decode("utf-8", "replace"):
                mojibake.append("%s(U+%04X)" % (rel, ord(token[0])))
    bad = []
    if bom:
        bad.append("含 BOM: %s" % "、".join(bom[:3]))
    if tab:
        bad.append("含 TAB: %s" % "、".join(tab[:3]))
    if mojibake:
        bad.append("疑似乱码: %s" % "、".join(mojibake[:3]))
    add("UTF-8 卫生（无 BOM/无 TAB/无乱码）", FAIL if bad else OK,
        "；".join(bad) or "%d 个文件干净" % len(files))


def checkVersion(files):
    vp = os.path.join(ROOT, "VERSION")
    if not os.path.exists(vp):
        add("VERSION 文件存在", FAIL, "仓库根缺 VERSION，发布无从校验")
        return
    ver = io.open(vp, encoding="utf-8").read().strip()
    if not re.fullmatch(r"v\d+\.\d+(-[0-9A-Za-z.]+)?", ver):
        add("VERSION 格式", FAIL, "不符合 v数字.数字[-标识]：%r" % ver)
        return
    add("VERSION 格式", OK, ver)
    try:
        r = subprocess.run(["git", "-C", ROOT, "describe", "--tags", "--abbrev=0"],
                           capture_output=True, text=True, timeout=30)
        tag = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        tag = ""
    if not tag:
        add("VERSION 与最近 tag 一致", WARN, "仓库还没有任何 tag，首次发版前先打 tag")
    else:
        add("VERSION 与最近 tag 一致", OK if tag == ver else FAIL,
            "VERSION=%s tag=%s" % (ver, tag))


def checkRecordTypeMap():
    """代码里的 rt→槽位/中文名映射，必须与 reference/frontend.md 表格对得上。"""
    from RecordCenter.RecordWrite import RECORD_TYPE_MAP, RECORD_TYPE_NAME
    md = os.path.join(ROOT, "reference", "frontend.md")
    text = io.open(md, encoding="utf-8").read() if os.path.exists(md) else ""
    if len(RECORD_TYPE_MAP) != 22 or len(RECORD_TYPE_NAME) != 22:
        add("rt 映射条数", FAIL, "RECORD_TYPE_MAP=%d RECORD_TYPE_NAME=%d（应为 22/22）"
            % (len(RECORD_TYPE_MAP), len(RECORD_TYPE_NAME)))
        return
    add("rt 映射条数", OK, "RECORD_TYPE_MAP / RECORD_TYPE_NAME 均为 22 项")
    drift = []
    for rt in sorted(RECORD_TYPE_MAP):
        row = [l for l in text.splitlines()
               if l.startswith("| %d |" % rt) or l.startswith("| %d " % rt)]
        if not row:
            drift.append("rt%s 在 frontend.md 缺行" % rt)
            continue
        if RECORD_TYPE_NAME[rt] not in row[0]:
            drift.append("rt%s 名称不符：%s" % (rt, RECORD_TYPE_NAME[rt]))
    add("frontend.md 与代码映射一致", FAIL if drift else OK,
        "；".join(drift[:3]) or "22 类的中文名与槽位表对得上")


def checkCli():
    bad = []
    for rel in CLI_ENTRIES:
        p = os.path.join(TOOLS, *rel.split("/"))
        if not os.path.exists(p):
            bad.append("%s 不存在" % rel)
            continue
        text = io.open(p, encoding="utf-8").read()
        if "__main__" not in text:
            bad.append("%s 无 __main__ 入口" % rel)
    add("命令行入口齐备（%d 个）" % len(CLI_ENTRIES), FAIL if bad else OK,
        "；".join(bad) or "全部具备 __main__ 入口")


def checkImport():
    try:
        import IqClient                              # noqa: F401
        from RecordCenter.RecordWrite import WriteMixin      # noqa: F401
    except Exception as e:                          # noqa: BLE001
        add("模块可导入（无副作用）", FAIL, "%s: %s" % (type(e).__name__, e))
        return
    add("模块可导入（无副作用）", OK, "IQClient 与写域 mixin 导入正常")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="只打印汇总行")
    a = ap.parse_args()

    files = repoFiles()
    checkNaming(files)
    checkSensitive(files)
    checkReferenceBudget()
    checkHygiene(files)
    checkVersion(files)
    checkRecordTypeMap()
    checkCli()
    checkImport()

    counts = {OK: 0, WARN: 0, FAIL: 0}
    for _n, st, _note in RESULTS:
        counts[st] += 1
    if not a.quiet:
        w = max(len(n) for n, _s, _t in RESULTS) + 2
        for n, st, note in RESULTS:
            print("  [%s] %-*s %s" % (st, w, n, note))
        print("-" * (w + 30))
    print("PASS=%d WARN=%d FAIL=%d 共 %d 项" % (counts[OK], counts[WARN],
                                                counts[FAIL], len(RESULTS)))
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())