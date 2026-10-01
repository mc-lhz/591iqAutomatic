# taskAndMessage（首页工作台）

管：待办/逾期/已办任务、未读消息、公告。
不管：任务详情与路由解析（`GET /task/get` + moduleId 映射，见 reference/api.md
「任务详情与路由解析」）。

## 对应端点

- `GET /task/count_task` — `{unfinished, expired, finished}`
- `GET /task/list` — status：0=待办 / 1=逾期未完成 / 2=已办；行含 `taskId/pcUrl`
- `GET /task/list_label` — 任务标签
- `GET /msg/queryUnRead` — 未读计数
- `GET /announcement/listAnnouncementRead` / `listPopupAnnouncementRead`

## 方法

| 方法 | 说明 |
|---|---|
| `taskStats()` | 三个计数 |
| `tasks(status="0", offset=0, limit=20, labelId="")` | 任务列表，status 取 0/1/2 |
| `unread()` | `{systemCount, favourCount, count, commentCount}` |
| `announcements(offset=0, limit=6)` | 公告列表 |

## 用法

```python
c.taskStats()                      # {'unfinished': 0, 'expired': 45, 'finished': 34}
c.tasks(status="0", limit=5)       # 待办；行内 pcUrl 自带 taskId + moduleId
```

## 注意事项

- `tasks()` 的 `page` 字段必须齐全（offset/limit/total/currentPage/totalPage），
  否则请求挂起超时。
- 写操作（提交活动总结）成功后 `unfinished` 会 -1 —— 这是闭环回执的一部分。