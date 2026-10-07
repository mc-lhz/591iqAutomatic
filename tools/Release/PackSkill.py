"""把仓库打成可分发的技能包 `591iqAutomatic.zip`（**根目录结构，不套外层目录**）。

与 GitHub 自动生成的源码包不同：那个是 `591iqAutomatic-<tag>/…` 套一层，
本脚本产出的 zip 里 `SKILL.md` / `tools/` / `reference/` 直接位于根目录。
代价是安装要自己先建目录再解压：
    mkdir -p ~/.config/opencode/skills/591iqAutomatic
    解压本 zip 到该目录

由 `.github/workflows/release.yml` 在 **Release 发布时**自动调用并挂为附件，
所以正常发版不需要手动跑这里；本模块同时供本地复现与 CI 校验。

用法：
    python tools/Release/PackSkill.py --list                    # 只看会打进哪些文件
    python tools/Release/PackSkill.py                           # 默认 %TEMP%\591iqAutomatic.zip
    python tools/Release/PackSkill.py --out dist/591iqAutomatic.zip
    python tools/Release/PackSkill.py --require-clean --version-check <tag> \\
            --out dist/591iqAutomatic.zip                        # CI 发版用；<tag> 传 tag 名（如 v0.1-beta2）

文件来源是 `git ls-files`，所以天然不含 .git / __pycache__ / *.pyc / 验证码图 /
state / 报告 json / xlsx；另见 EXCLUDE_PREFIXES 与 EXCLUDE_GLOBS。

⚠️ 本模块**不注册进 IQClient 门面**：它与 591iq 平台 API 无关，属仓库维护工具。
这是 AGENTS.md「新业务域 = mixin + 门面注册」的唯一显式例外。

退出码：0 成功 / 2 打包后自检不合规 / 3 前置条件不满足（脏工作区、版本不匹配、非 git 仓库）
"""
import argparse
import fnmatch
import hashlib
import io
import os
import re
import subprocess
import sys
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))                # 仓库根

PKG_NAME = "591iqAutomatic.zip"
# 这些是仓库内部约定/流水线配置，随包分发没有意义
EXCLUDE_PREFIXES = (".github/",)
EXCLUDE_EXACT = (".gitignore",)
# 兜底：即使将来某个 junk 被误提交，也拦在包外
EXCLUDE_GLOBS = ("__pycache__/*", "*/__pycache__/*", "*.pyc", "*.pyo",
                 "*.state.json", "*.vision.png", "*.jpg", "*.png", "*.xlsx",
                 "jcaptcha*", "vl_*", "*ApiReadOnlyReport.json", "*Dump.txt",
                 "591iq_*.json")
# 结构自检：这些必须**不存在**于包内
FORBIDDEN_GLOBS = ("__pycache__/*", "*/__pycache__/*", "*.pyc", ".git/*",
                   "*.state.json", "*.vision.png", "*.jpg", "*.png", "*.xlsx",
                   ".github/*", "*/.git/*",
                   # Tier 3 受限文档：越权端点细节与探测手法。它已被 .gitignore
                   # 挡住（git ls-files 拿不到），这里再加一道是防「哪天有人
                   # 手工 git add -f 了」——合规文件漏进包比漏进仓库更难发现。
                   "reference/api-privileged.md")
MUST_HAVE = ("SKILL.md", "AGENTS.md", "README.md", "VERSION")


def run_git(*args):
    r = subprocess.run(["git", "-C", ROOT] + list(args),
                       capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout


def excluded(rel):
    if rel in EXCLUDE_EXACT or rel.startswith(EXCLUDE_PREFIXES):
        return True
    name = os.path.basename(rel)
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g)
               for g in EXCLUDE_GLOBS)


def collect():
    """返回 [(仓库相对路径, 绝对路径)]，按路径排序。"""
    code, out = run_git("ls-files")
    if code != 0:
        raise SystemExit("[pack] 不是 git 仓库或 git 不可用，无法按git ls-files 取文件")
    got = []
    for rel in out.split("\n"):
        rel = rel.strip().replace("\\", "/")
        if not rel or excluded(rel):
            continue
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            got.append((rel, p))
    return sorted(got)


def checkPrereqs(requireClean, versionCheck):
    if requireClean:
        code, out = run_git("status", "--porcelain", "--untracked-files=no")
        if code != 0:
            raise SystemExit("[pack] git status 失败，无法校验工作区是否干净")
        if out.strip():
            names = [re.sub(r"^..\s+", "", l).strip()
                     for l in out.strip().split("\n")[:5]]
            raise SystemExit("[pack] 工作区有未提交改动，拒绝打包：%s\n"
                             "        （要打脏包请去掉 --require-clean）"
                             % "、".join(names))
    if versionCheck:
        vp = os.path.join(ROOT, "VERSION")
        if not os.path.exists(vp):
            raise SystemExit("[pack] 仓库根缺 VERSION，无法校验版本")
        ver = io.open(vp, encoding="utf-8").read().strip()
        if ver != versionCheck.strip():
            raise SystemExit("[pack] VERSION(%s) 与 tag(%s) 不一致——"
                             "版本号唯一落点是 VERSION，发版前必须先改它"
                             % (ver, versionCheck))


def verify(zpath, expect):
    """重新打开 zip 做结构自检，返回问题列表（空 = 合规）。"""
    bad = []
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        for must in MUST_HAVE:
            if must not in names:
                bad.append("根目录缺少 %s" % must)
        tops = {n.split("/", 1)[0] for n in names}
        # 根目录包不该只有一层同名目录（那就是 GitHub 源码包的结构）
        if len(tops) == 1 and "/" not in names[0]:
            bad.append("疑似套了一层目录（顶层只有 %s），应为根目录包" % list(tops)[0])
        for n in names:
            if any(fnmatch.fnmatch(n, g) or fnmatch.fnmatch(os.path.basename(n), g)
                   for g in FORBIDDEN_GLOBS):
                bad.append("包内含不该有的文件：%s" % n)
        if len(names) != expect:
            bad.append("条目数不符：写入 %d，zip 内 %d" % (expect, len(names)))
    return bad


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build(outPath, requireClean=False, versionCheck=""):
    checkPrereqs(requireClean, versionCheck)
    files = collect()
    if not files:
        raise SystemExit("[pack] 没有可打包的文件")
    outDir = os.path.dirname(os.path.abspath(outPath))
    if outDir and not os.path.isdir(outDir):
        os.makedirs(outDir, exist_ok=True)
    with zipfile.ZipFile(outPath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, p in files:
            z.write(p, rel)
    bad = verify(outPath, len(files))
    if bad:
        print("[pack] 打包后自检不合规：", file=sys.stderr)
        for b in bad:
            print("   !! " + b, file=sys.stderr)
        return 3, None
    size = os.path.getsize(outPath)
    digest = sha256(outPath)
    return 0, {"count": len(files), "size": size, "sha256": digest,
               "out": os.path.abspath(outPath)}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="输出 zip 路径（默认系统临时目录下的 %s）" % PKG_NAME)
    ap.add_argument("--list", action="store_true", help="只列出将打包的文件，不写 zip")
    ap.add_argument("--require-clean", action="store_true",
                    help="工作区有未提交的已跟踪改动就拒绝打包（CI 用）")
    ap.add_argument("--version-check", default="",
                    help="要求 VERSION 内容与该值逐字相同（传 tag 名），否则失败")
    a = ap.parse_args()

    files = collect()
    if a.list:
        total = 0
        for rel, p in files:
            total += os.path.getsize(p)
        print("将打包 %d 个文件 / %.1f KB（根目录结构，不套外层目录）"
              % (len(files), total / 1024))
        for rel, p in files:
            print("  %7d  %s" % (os.path.getsize(p), rel))
        print("已排除：%s、以及 .gitignore"
              % "、".join(EXCLUDE_PREFIXES))
        return 0

    out = a.out or os.path.join(os.environ.get("TEMP", os.getcwd()), PKG_NAME)
    code, info = build(out, a.require_clean, a.version_check)
    if code:
        return code
    print("[pack] 完成：%s" % info["out"])
    print("  文件数     : %d" % info["count"])
    print("  体积       : %.1f KB" % (info["size"] / 1024))
    print("  sha256     : %s" % info["sha256"])
    print("  结构       : 根目录（SKILL.md / tools/ / reference/ 直接在顶层）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:                                # noqa: BLE001
        print("[pack] 异常: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)