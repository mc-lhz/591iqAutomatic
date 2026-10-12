"""自证：把红线项的三条判据分别破坏掉，确认 TestContract 会 FAIL。

合规检查本身也会失灵——如果它恒 PASS，那就是装饰品。
"""
import io
import os
import shutil
import sys
import tempfile

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools"))
sys.path.insert(0, os.path.join(SKILL, "tools", "TestCases"))

import TestContract as TC          # noqa: E402


def run():
    TC.RESULTS.clear()
    TC.checkCapabilityGate()
    return TC.RESULTS[-1][1], TC.RESULTS[-1][2]


def main():
    print("① 现状（应 PASS）")
    print("   ", run())

    print("\n② 往门面塞回 commitBatchVote（应 FAIL）")
    from IqClient import IQClient
    IQClient.commitBatchVote = lambda self, *a, **k: {}
    try:
        print("   ", run())
    finally:
        del IQClient.commitBatchVote

    print("\n③ 重建 Selection 目录（应 FAIL）")
    sel = os.path.join(SKILL, "tools", "Selection")
    os.makedirs(sel, exist_ok=True)
    open(os.path.join(sel, "__init__.py"), "w").close()
    try:
        print("   ", run())
    finally:
        shutil.rmtree(sel, ignore_errors=True)

    print("\n④ 破坏默认脱敏（应 FAIL）")
    from SearchCenter import SearchQuery
    orig = SearchQuery.SearchMixin.searchRecords
    SearchQuery.SearchMixin.searchRecords = lambda self, kw, **k: {"list": [
        {"userInf": {"idNumber": "0" * 18, "userName": "A"}}]}
    try:
        print("   ", run())
    finally:
        SearchQuery.SearchMixin.searchRecords = orig

    print("\n⑤ 还原后（应回到 PASS）")
    print("   ", run())


if __name__ == "__main__":
    main()