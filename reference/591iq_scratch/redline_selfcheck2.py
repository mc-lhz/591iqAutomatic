"""红线自证 v2：逐条破坏，确认 TestContract 会 FAIL。

上一版自证证明「检查会红」；这版补上新加的三条（非法 type_ / 归属校验 /
queryRecord 脱敏）。合规检查若恒 PASS 就是装饰品，所以必须先证明它会红。
"""
import os
import sys

SKILL = r"C:\Users\Administrator\.config\opencode\skills\591iqAutomatic"
sys.path.insert(0, os.path.join(SKILL, "tools"))
sys.path.insert(0, os.path.join(SKILL, "tools", "TestCases"))

import TestContract as TC                                    # noqa: E402
from RecordCenter import RecordQuery as RQ                   # noqa: E402
from SearchCenter import SearchQuery as SQ                   # noqa: E402


def run(tag):
    TC.RESULTS.clear()
    TC.checkCapabilityGate()
    st, note = TC.RESULTS[-1][1], TC.RESULTS[-1][2]
    print("%-34s %-4s %s" % (tag, st, note[:88]))
    return st


def main():
    print("① 现状（应 PASS）")
    run("baseline")

    print("\n② 放行非法 type_（应 FAIL）")
    orig_records = RQ.QueryMixin.records
    RQ.QueryMixin.records = orig_records.__wrapped__ if hasattr(
        orig_records, "__wrapped__") else _passthroughRecords()
    try:
        run("records 去掉白名单")
    finally:
        RQ.QueryMixin.records = orig_records

    print("\n③ 去掉 queryRecord 归属校验（应 FAIL）")
    orig_qr = RQ.QueryMixin.queryRecord
    RQ.QueryMixin.queryRecord = _noOwnerCheck()
    try:
        run("queryRecord 不校验归属")
    finally:
        RQ.QueryMixin.queryRecord = orig_qr

    print("\n④ queryRecord 不脱敏（应 FAIL）")
    RQ.QueryMixin.queryRecord = _noRedact()
    try:
        run("queryRecord redact=False 变默认")
    finally:
        RQ.QueryMixin.queryRecord = orig_qr

    print("\n⑤ 还原后（应回到 PASS）")
    run("restored")


def _passthroughRecords():
    def records(self, offset=0, limit=10, recordType="", labelId="",
                type_="2", userName="", redact=True, unsafeScope=False):
        return self.post("/record/queryRecordList", {
            "type": type_, "recordType": recordType, "labelId": labelId,
            "offset": offset, "limit": limit, "userName": userName})
    return records


def _noOwnerCheck():
    def queryRecord(self, recordId, redact=True, allowOther=True):
        rec = self.post("/record/queryRecord", {"id": recordId})["list"]
        return RQ.redactUserInf(rec, redact)
    return queryRecord


def _noRedact():
    def queryRecord(self, recordId, redact=False, allowOther=True):
        return self.post("/record/queryRecord", {"id": recordId})["list"]
    return queryRecord


if __name__ == "__main__":
    main()