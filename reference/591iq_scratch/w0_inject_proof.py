"""临时在 README.md 注入一处真实姓名形态，验证 TestContract 新闸门真会 FAIL，然后还原。"""
import io
import os
import subprocess
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
TARGET = os.path.join(ROOT, "README.md")
INJECT = "\n临时验证行：林昊哲（2 封）\n"

env = dict(os.environ, PYTHONIOENCODING="utf-8")
with io.open(TARGET, encoding="utf-8", newline="") as f:
    orig = f.read()
try:
    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.write(orig + INJECT)
    r = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(ROOT, "tools/TestCases/TestContract.py")],
                       capture_output=True, text=True, env=env,
                       encoding="utf-8", errors="replace", cwd=ROOT, timeout=900)
    hit = [x for x in r.stdout.splitlines() if "敏感串" in x]
    summary = [x for x in r.stdout.splitlines() if x.startswith("PASS=")]
    print("INJECTED_RESULT:", (hit[0].strip() if hit else "(no sensitive line)"))
    print("INJECTED_SUMMARY:", summary[0] if summary else "(none)")
    print("VERDICT:", "GATE_WORKS" if hit and "FAIL" in hit[0] else "GATE_IS_FAKE")
finally:
    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.write(orig)
    print("RESTORED_README")