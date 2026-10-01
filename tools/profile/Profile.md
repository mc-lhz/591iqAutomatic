# Profile（学生档案域）

管：当前登录学生的档案详情、家长、兴趣特长。
不管：平台字典（见 `meta/Options.py`）、任务（`workbench/`）、记录（`record/`）。

## 对应端点（reference/api.md）

- `GET /user/getUserInfoDetail` — 档案详情（49 键：姓名/学籍号/生日/班级/学校…）
- `GET /studentMgr/getParentList` — 家长列表
- `GET /statistics/student/get_interest` — 兴趣特长（艺术/体育/专业方向）

## 方法

| 方法 | 说明 |
|---|---|
| `userInfo()` | 本人档案 49 键详情（sex/birthday/className/schoolName…） |
| `parents()` | 家长列表 |
| `interests()` | 兴趣特长：艺术爱好、体育爱好、专业方向 |

## 用法

```python
from IqClient import IQClient
c = IQClient("<ssoToken>"); c.login()
c.userInfo()["className"]
c.parents()
c.interests()
```

## 注意事项

- `userId` 属性来自 `login()` 返回，未登录会抛 TypeError。
- 档案数据含学生个人信息（姓名/生日/证件号），只取所需字段，不要整包落库。