"""去掉 PowerShell Set-Content 写出的 BOM，并补回末尾换行（AGENTS.md 记的坑）。"""
import io
import sys

for p in sys.argv[1:]:
    raw = open(p, "rb").read()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if had_bom else raw
    nl = b""
    if not body.endswith(b"\n"):
        nl = b"\n"
        body += nl
    if had_bom or nl:
        with io.open(p, "wb") as f:
            f.write(body)
    print("%s bom_removed=%s newline_added=%s" % (p, had_bom, bool(nl)))