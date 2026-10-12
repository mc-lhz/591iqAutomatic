"""干净地跑 verify 并抓失败项（绕开 PowerShell 编码）。"""
import os
import subprocess
import sys

P = r"C:\Users\Administrator\Desktop\PersonalPage"
NPM = r'C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\npm.cmd'
NODE = r'C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\node.exe'
env = dict(os.environ, PYTHONIOENCODING='utf-8')

b = subprocess.run([NPM, "run", "build"], cwd=P, capture_output=True,
                   env=env, timeout=600)
print("build exit=%d" % b.returncode)
if b.returncode:
    sys.stdout.write(b.stderr.decode("utf-8", "replace")[-2000:])

v = subprocess.run([NODE, "scripts/verify-build.mjs"], cwd=P, capture_output=True,
                   env=env, timeout=300)
out = v.stdout.decode("utf-8", "replace")
lines = out.split("\n")
print("verify exit=%d" % v.returncode)
print("\n=== 失败项（✗）===")
for i, ln in enumerate(lines):
    if "\u2717" in ln:
        for j in range(max(0, i - 2), min(len(lines), i + 3)):
            print("   " + lines[j][:150])
        print("   ---")
print("\n=== 汇总行 ===")
for ln in lines[-6:]:
    print("   " + ln[:150])