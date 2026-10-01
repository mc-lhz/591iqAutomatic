# Write（写实记录·写）

管：图片上传、写实记录发布（活动 / 荣誉 / 其余 19 种 recordType）。
⚠️ **全是写操作**：记录进本校可见 feed，学生端无删除接口，调用前必须向用户确认。

## 对应端点

- `POST /announcement/upload` — 图片上传 → `https://fs.591iq.cn/...`
- `POST /record/updateRecord` — 发布/编辑写实记录（同一接口）

## 方法

| 方法 | 说明 |
|---|---|
| `uploadImage(pathOrBytes, filename="image.jpg", mime="image/jpeg", objType="25")` | 上传图片，返回 imageUrl |
| `addRecord(recordContent, typeForm, recordType)` | 底层发布；`recordType` 数字 → 槽位名查 `RECORD_TYPE_MAP` |
| `publishActivity(semesterCode, name, labelId, level, beginTime, endTime, address, duration, roleId, content, images=None, recordType="17", dimensionId="", addressId="", extraContent=None)` | 活动记录完整表单 |
| `publishHonor(semesterCode, typeId, typeName, honorTime, sponsor, levelId, levelName, itemName, content, honorImages, orderName="", recordType="1", orderId="")` | 荣誉记录完整表单 |

内部常量：`RECORD_TYPE_MAP`（recordType → 组件槽位名）、`RECORD_TYPE_NAME`（中文名）。
内部辅助：`_semesterName(code)` 由 `semesterOptions()` 反查学期名。

## 用法

```python
img = c.uploadImage("photo.jpg")
c.publishActivity(semesterCode="3", name="研究性学习", labelId=29, level="01",
                   beginTime="2026-10-01", endTime="2026-10-02",
                   address="厦门一中", duration=2, roleId=3,
                   content="……", images=[img], dimensionId="17")
```

## 注意事项

- **顶层槽位 key 必须是组件名**（`recordActivityFJ`/`recordHonor`…），数字只写在
  `recordContent.recordType` 里；传数字 key → `999999 发布失败`。
- 图片必须自己上传（`uploadImage`）；复用他人 fs URL 是否触发 999999 未证实。
- `labelId` / `typeId` / `levelId` 取值查 `dictOptions/Options.py`，不要硬编码。
- **成功判据 = 读回执**：返回 `{"list":"操作成功"}` 不代表生效，要读回列表/统计核对。
- 活动总结（`/evaluateActivity/submitSummary`）不在此模块，见 reference/api.md「写入接口②」。