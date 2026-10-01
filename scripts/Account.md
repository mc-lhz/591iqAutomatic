# Account（账号域）

管：当前登录用户的基本信息、数据字典、学期选项。
不管：任务、记录、成长、写入（分别见 Tasks / Records / Grow / Publish）。

## 对应端点（reference/api.md）

- `GET /user/getUserInfoDetail` — 基本信息、学籍号、生日等
- `GET /sysDict/getDict` — 字典（SemesterCode / RecordHonorOrder / INTEREST …）

## 方法

| 方法 | 说明 |
|---|---|
| `userInfo()` | 当前用户 49 键详情（sex/birthday/className/schoolName…） |
| `sysDict(field)` | 取指定字典，返回 `pdlist` |
| `semesterOptions()` | `sysDict("SemesterCode")` 的快捷方式 → `{'1':'高一上',…,'6':'高三下'}` |

## 用法

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()
c.userInfo()["className"]
c.semesterOptions()["3"]   # '高二上'
```

## 注意事项

- `userId` 属性来自 `login()` 返回，未登录会抛 TypeError。
- 字典接口返回 `pdlist`（不是 `list`）。
