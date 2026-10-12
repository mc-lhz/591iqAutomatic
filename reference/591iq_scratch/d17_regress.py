"""D17 回归自证：新闸门在旧实现下必须 FAIL，否则这条检查是假的。"""
import os
import sys

ROOT = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "TestCases"))

from Access.HttpTransport import IQError, unwrapEnvelope   # noqa: E402
import TestContract as TC                                 # noqa: E402


def oldUnwrap(out, path):
    """修复前的 _call 尾部逻辑（只查顶层 code），用来验证闸门能抓住它。"""
    if not isinstance(out, dict):
        return out          # 裸数组保护是本次附带新增，与 D17 无关，先补上以聚焦
    if out.get("code") not in (0, "0", None):
        if out.get("code") == 9000:
            raise IQError("session已过期")
        raise IQError("%s -> code=%s msg=%s" % (path, out.get("code"), out.get("msg")))
    return out.get("data", out)


payload = {"meta": {"code": 1, "msg": "学生总结已截止"}, "data": None}
TC.RESULTS.clear()
import Access.HttpTransport as HT              # noqa: E402
HT.unwrapEnvelope = oldUnwrap                   # checkEnvelope 每次现 import，必须改模块属性
TC.checkEnvelope()
print("[旧实现]", TC.RESULTS[-1])
HT.unwrapEnvelope = unwrapEnvelope

print("[新实现]", unwrapEnvelope({"code": 0, "data": {"ok": 1}}, "/p"))
try:
    unwrapEnvelope(payload, "/p")
    print("[新实现] meta 失败 -> 未抛，BUG")
except IQError as e:
    print("[新实现] meta 失败 -> IQError:", e)
