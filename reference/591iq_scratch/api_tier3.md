# 受限能力文档（不进公开仓库）

本文件是**能力分层里的 Tier 3**：记录需要在授权前提下使用的能力与端点细节。

## 为什么不进公开仓库

1. **D14 是未修复的平台漏洞**。把越权端点的完整路径与调用方式公开发布，
   等于替攻击者做侦察。披露应走「发现 → 私下报给平台 → 等修复或接受风险」，
   而不是贴在公开仓库里等人来取。
2. **人员枚举能力默认关闭**（见 `SearchQuery` 模块文档）。真正的使用方法、
   授权流程与实测规模只应让确有授权的人看到。
3. **厂商内部构件编号**（chunk / moduleId）随 `recordForms.json` 在公开仓库里，
   对使用者零价值，却是可主张的知识产权载体。

打包规则：`Release/PackSkill.py` 按 `git ls-files` 取文件，本文件被 `.gitignore`
排除，因此**不会进入发布包**；`TestContract.py` 的「技能包结构合规」每次 CI 都验这一点。

## Tier 3-a：越权端点（已发现，待平台修复）

| 端点 | 现象 |
|---|---|
| `/apps/credit/query/list_school` | 教师端学分名册，**学生 token 可读**，返回全校 `studentName` + `idNumber` + `className`（实测 28,705 条级）。跨角色越权，涉及未成年人敏感个人信息 |

上报状态：已起草 security 工单（`SendFeedback.py --type security`），
**待用户确认后投递到平台官方渠道**。本地工具未批量留存该数据。

> 工具侧不做这个端点的封装，也不做探测脚本——它是漏洞不是功能。
> 一次读回验证即可，不重复抓取。

## Tier 3-b：人员枚举（需授权，默认关闭）

`searchPeople()` / `findPeople()`（`/search/search` type=2）能在全校范围枚举他人。
实测规模：跨 407 个汉字去重得 28,190 人，`schId` 恒为本校（租户由 AccessToken 决定）。

开启方式（两种都会在 stderr 留 WARNING）：

```python
c.enablePeopleSearch("校方德育处口头许可 2026-10")   # 必须写明授权来源
# 或
$env:IQ_ALLOW_PEOPLE_SEARCH = "1"                    # 脚本场景，同样留痕
```

使用约束：
- 一次授权只用于一个明确任务，不长期开着；
- 结果只在本地用于当前任务，**不落盘、不外传、不二次分发**；
- 需要按姓名定位某人时，优先用 `records(type_="2")` 的班级 feed 拿 userId，
  那是 UI 本来就有的范围。

## Tier 3-c：记录搜索的原始返回（D10）

`searchRecords(..., redact=False)` 返回每条命中内嵌 51 字段的 `userInf`，
含 `idNumber`、考号、照片 URL 等。默认已脱敏（2026-10-06 起），按需再放开。