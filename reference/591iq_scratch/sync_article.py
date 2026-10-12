"""把新的安全措施同步进那篇《591iq隐私安全设计》正文 HTML。

原则：
  · 所有 <svg> 配图**原样保留**（用户要求「配图不用改」）——图里过期的数字
    改在紧邻的文字里说明，不动图本身。
  · 只改事实已过期的文字/表格 + 新增两个机制小节 + 重写「已知缺口」与结论。
"""
import io
import os
import sys

SRC = os.path.join(os.environ["TEMP"], "591iq_scratch", "article_old.html")
DST = os.path.join(os.environ["TEMP"], "591iq_scratch", "article_new.html")

h = io.open(SRC, encoding="utf-8").read()
before_svg = h.count("<svg")
done, miss = [], []


def sub(old, new, tag):
    global h
    if old in h:
        h = h.replace(old, new, 1)
        done.append(tag)
    else:
        miss.append(tag)


# ---------- 头部元信息 ----------
sub('<span>文档版本：<b>v0.1-beta1</b></span>',
    '<span>文档版本：<b>v0.1-beta2</b>（2026-10-06 安全增补）</span>',
    "版本号")

sub('<p class="lede">面对一个会接触 <b>学号、姓名、班级、身份证号、成绩、成长档案</b> 等高度敏感学生数据的技能，本项目把“保护学生隐私”落实成 <b>文档层制度 + 代码层机制 + 智能审计</b> 三道防线，而非一句口号。</p>',
    '<p class="lede">面对一个会接触 <b>学号、姓名、班级、身份证号、成绩、成长档案</b> 等高度敏感学生数据的技能，本项目把“保护学生隐私”落实成 <b>文档层制度 + 代码层机制 + 智能审计</b> 三道防线，而非一句口号。<br>'
    '2026-10-06 增补：在原有三道防线之外，新增 <b>能力边界</b>（对服务端宽于前端的接口做客户端收口）与 <b>可观测留痕</b>（危险操作必留 WARNING 日志）两套机制，并把发现的平台侧越权漏洞按<b>安全工单</b>正式上报。</p>',
    "导语")

# ---------- 第五节：审计闸门数据刷新 ----------
sub('<p>项目内置 <code>TestContract.py</code>，在<b>离线、无网络、无凭据</b>环境下执行 13 项契约与卫生检查，作为每次 CI 的硬性隐私闸门。实测结果：<b>11 PASS / 2 WARN / 0 FAIL</b>。</p>',
    '<p>项目内置 <code>TestContract.py</code>，在<b>离线、无网络、无凭据</b>环境下执行契约与卫生检查，作为每次 CI 的硬性隐私闸门。'
    '2026-10-06 实测：<b>15 项 · 14 PASS / 1 WARN / 0 FAIL</b>（<code>--strict</code> 退出码 0）。</p>'
    '<p style="margin-top:8px;font-size:13px;color:#7d8da8">'
    '（图 5 绘制于 2026-10-04，列出的检查项为其子集；此后新增了「响应信封」与「能力红线」两项，见下方机制六、七。）</p>',
    "第五节导语")

sub('<div class="mech"><h3><span class="dot"></span>发版前置</h3><ul><li>发版前必跑 <code>compileall</code> + 契约自检 + 敏感串扫描</li><li>线上回归（只读 41+ 项）在本地执行</li></ul></div>',
    '<div class="mech"><h3><span class="dot"></span>发版前置</h3><ul><li>发版前必跑 <code>compileall</code> + 契约自检 + 敏感串扫描</li>'
    '<li>线上回归（只读 <b>47 项</b>）在本地执行</li></ul></div>',
    "发版前置")

# ---------- 第六节之后插入两个新机制 ----------
NEW_MECH = '''
  <!-- 7 新增 机制六：能力边界 -->
  <section>
    <div class="sec-h"><div class="n">7</div><h2>机制六 · 能力边界</h2><span class="sub">高敏能力默认关闭 / 不留后门</span></div>
    <div class="card">
      <p>审计发现平台有若干接口<b>比学生端前端宽松</b>：前端没有的入口、传非法参数就能拿到的更大数据面。这些属于「超出界面设计」的范围扩大。处理原则是：<b>能删就删，删不掉就收口，收口必须留痕</b>。</p>
      <table style="margin-top:10px">
        <colgroup><col><col><col></colgroup>
        <thead><tr><th>能力</th><th>处置</th><th>理由</th></tr></thead>
        <tbody>
          <tr><td>全校人员搜索<br><span style="font-size:12px;color:#7d8da8">一次调用可枚举全校学生（实测去重 28,190 人级），原始返回含身份证号、考号、照片、班级干部与政治面貌</span></td>
              <td><span class="danger">整体删除</span></td>
              <td>一次调用即把全校人员目录变成可枚举数据源，而使用者是单个学生账号</td></tr>
          <tr><td>遴选/投票<br><span style="font-size:12px;color:#7d8da8">批量投票改的是他人遴选结果；强制确认可替报告发起人操作，已证实投票窗口过期后仍可确认</span></td>
              <td><span class="danger">整体删除</span></td>
              <td>越权代操作，且不可撤销</td></tr>
          <tr><td>记录列表非法 <code>type</code></td>
              <td><span class="ok">客户端白名单</span></td>
              <td>空串/任意非法值走服务端<b>无过滤兜底分支</b>，实测 146,020 条，约为「学校」页的 12 倍，含历年毕业届记录，每行带作者姓名与班级</td></tr>
          <tr><td>记录详情不校验归属</td>
              <td><span class="ok">客户端归属校验</span></td>
              <td>服务端只按 id 返回、不校验归属，且返回体含 51 个身份字段</td></tr>
        </tbody>
      </table>
      <div class="grid2" style="margin-top:12px">
        <div class="mech"><h3><span class="dot"></span>删除而非开关</h3><ul>
          <li>上述两项高敏能力<b>整体删除代码与用例</b></li>
          <li><b>刻意不留环境变量旁路</b>——留后门等于「藏起来但没关掉」，反而诱导绕过</li>
          <li>正当需求有替代路径：取某人用户 ID 走「班级」范围即可，无需全校搜人</li></ul></div>
        <div class="mech"><h3><span class="dot"></span>收口可被显式绕开，但必留痕</h3><ul>
          <li>确需更大范围时须<b>显式传参</b>（<code>unsafeScope=True</code> / <code>allowOther=True</code>）</li>
          <li>每次绕开都打 <b>WARNING 日志</b>，本地可审计</li>
          <li>不提供静默绕过</li></ul></div>
      </div>
      <p style="margin-top:12px;font-size:13.5px;color:#3f5170"><b>诚实说明：</b>这两道客户端闸门<b>只防误用、不是安全控制</b>。绕过本工具直接发 HTTP 请求，依然能拿到全量数据——因为宽松的是服务端。真正的修复必须在平台侧，故已按安全工单上报（见机制七）。</p>
    </div>
  </section>

  <!-- 8 新增 机制七：可观测与上报 -->
  <section>
    <div class="sec-h"><div class="n">8</div><h2>机制七 · 可观测与安全上报</h2><span class="sub">留痕 · 自证 · 善意披露</span></div>
    <div class="card">
      <div class="grid2">
        <div class="mech"><h3><span class="dot"></span>详细 DEBUG 日志</h3><ul>
          <li>每次请求记录方法、路径、参数键、响应码、<b>耗时</b>；网络异常记录完整调用栈</li>
          <li>默认等级 WARNING，<b>默认什么都不输出</b>，不影响用户可见结论</li>
          <li>用 <code>--verbose</code> 或环境变量开启</li></ul></div>
        <div class="mech"><h3><span class="dot"></span>闸门自证</h3><ul>
          <li>合规检查若恒为 PASS，就是装饰品</li>
          <li>因此<b>逐条破坏红线并验证 CI 会变红</b>：移除白名单→FAIL、移除归属校验→FAIL、关闭脱敏→FAIL、还原→PASS</li>
          <li>检查项本身每迭代重跑一次</li></ul></div>
      </div>
      <div style="margin-top:12px">
        <h3 style="font-size:15px;margin-bottom:8px"><span class="dot" style="display:inline-block"></span>向平台上报的两条安全工单</h3>
        <table>
          <colgroup><col><col><col></colgroup>
          <thead><tr><th>编号</th><th>问题</th><th>处置</th></tr></thead>
          <tbody>
            <tr><td><b>D14</b></td><td>教师端学分名册接口，学生角色令牌可直接调用，返回全校学生姓名、身份证号、班级</td>
                <td><span class="ok">已投递安全工单</span>，工单内容经脱敏闸门校验，不含任何真实个人信息</td></tr>
            <tr><td><b>D19</b></td><td>记录详情不校验归属（返回 51 个身份字段）＋ 记录列表非法参数走无过滤兜底分支</td>
                <td><span class="ok">已投递安全工单</span>，并在工具侧加客户端闸门</td></tr>
          </tbody>
        </table>
      </div>
      <p style="margin-top:12px;font-size:13.5px;color:#3f5170"><b>披露原则：</b>只披露最小必要信息——<b>端点路径与调用载荷不写入公开文档与发布包</b>，漏洞细节单独存放且不随包分发；工单正文只写现象、复现、影响与修复建议，字段仅列<b>名称</b>不列<b>值</b>。</p>
    </div>
  </section>
'''

anchor = '  <!-- 7 文档层制度 -->'
sub(anchor, NEW_MECH.strip("\n") + "\n\n" + anchor, "插入机制六/七")

sub('<div class="n">7</div><h2>文档层制度</h2>', '<div class="n">9</div><h2>文档层制度</h2>', "文档层制度号")
sub('<div class="n">8</div><h2>代码层实现对照</h2>', '<div class="n">10</div><h2>代码层实现对照</h2>', "代码层号")
sub('<div class="n">9</div><h2>已知缺口（如实标注）</h2>', '<div class="n">11</div><h2>已知缺口（如实标注）</h2>', "缺口号")
sub('<div class="n">10</div><h2>设计结论</h2>', '<div class="n">12</div><h2>设计结论</h2>', "结论号")

# ---------- 代码层实现对照表 ----------
sub('<tr><td><code>TestCases/TestContract.py</code></td><td>敏感串扫描、结构审计、无副作用导入</td><td><span class="ok">11 PASS / 0 FAIL</span></td></tr>',
    '<tr><td><code>TestCases/TestContract.py</code></td><td>敏感串扫描、结构审计、无副作用导入、能力红线、响应信封</td><td><span class="ok">15 项 14 PASS / 0 FAIL</span></td></tr>\n'
    '          <tr><td><code>RecordCenter/RecordQuery.py</code></td><td>记录列表范围白名单、详情归属校验、身份字段默认脱敏</td><td><span class="ok">已实测·CI 红线守护</span></td></tr>\n'
    '          <tr><td><code>SearchCenter/SearchQuery.py</code></td><td>仅保留记录搜索；人员枚举能力<b>整体删除</b>，命中项默认脱敏</td><td><span class="ok">已实测·CI 红线守护</span></td></tr>\n'
    '          <tr><td><code>Common/Logcat.py</code></td><td>详细 DEBUG / WARNING 审计留痕；仅密码与证件号强制脱敏</td><td><span class="ok">已接入三处调用方</span></td></tr>',
    "代码层表")

# ---------- 已知缺口重写 ----------
OLD_GAP_START = '          <tr><td><b>D2</b></td>'
i = h.find(OLD_GAP_START)
j = h.find('</tbody>', i)
NEW_GAP = '''          <tr><td><b>D14</b> / <b>D19</b></td>
              <td>平台侧角色校验缺失：教师端名册接口学生令牌可读；记录详情不校验归属；记录列表非法参数走无过滤兜底分支</td>
              <td><span class="danger">平台侧未修</span>。工具侧已加客户端闸门，但<b>绕过工具直连仍可拿全量</b>；已投递安全工单等待修复</td></tr>
          <tr><td><b>D5</b></td><td>活动总结删除接口对不存在的 ID 仍返回 <code>code=0</code>，无异常保护</td>
              <td><span class="danger">删除类需二次确认</span>，返回值不可当成功判据</td></tr>
          <tr><td>—</td><td>导出 xlsx 含本人姓名/班级/成绩等个人信息</td>
              <td><span class="warn">仅限本人本地使用</span></td></tr>
          <tr><td>—</td><td>上传到平台图床的图片 URL 可被访问</td>
              <td><span class="warn">公开存储，发布前确认内容</span></td></tr>
          <tr><td>—</td><td>本次上报走的是作者自建反馈服务，未直接送达平台方</td>
              <td><span class="warn">工单已留痕，正式渠道待跟进</span></td></tr>
'''
h = h[:i] + NEW_GAP + h[j:]
done.append("已知缺口表重写")

# ---------- 结论重写 ----------
OLD_CONC = ('      <p><b>本项目把“学生隐私安全”落实为制度 + 机制 + 审计三重保险：</b>文档层规定“什么不许入库、什么不许外传、写前必须确认”；'
            '代码层用<b>凭据不落盘、网络白名单、写操作确认+读回执、最小权限、用完即焚</b>五道机制强制执行；'
            '智能审计在 CI 中持续拦截敏感串与结构风险。整体设计克制、安全、可审计。</p>\n'
            '      <p style="margin-top:10px">唯一明显短板是 <b>D2（搜索接口未脱敏）</b> 与 <b>D5（删除无异常保护）</b>，'
            '使用搜索 / 删除功能时需格外留意，这也是本项目“如实标注缺口”这一安全态度的体现。</p>')
NEW_CONC = ('      <p><b>本项目把“学生隐私安全”落实为制度 + 机制 + 审计三重保险：</b>文档层规定“什么不许入库、什么不许外传、写前必须确认”；'
            '代码层用<b>凭据不落盘、网络白名单、写操作确认+读回执、最小权限、用完即焚</b>五道机制强制执行；'
            '智能审计在 CI 中持续拦截敏感串与结构风险。2026-10-06 起再补两套：'
            '<b>能力边界</b>（高敏能力整体删除而非留开关；服务端宽于前端的接口做客户端收口）与'
            '<b>可观测留痕</b>（危险操作必留 WARNING、闸门逐条自证会失败、漏洞按工单上报且不公开载荷）。'
            '整体设计克制、安全、可审计。</p>\n'
            '      <p style="margin-top:10px"><b>当前最大短板不再是工具，而是平台侧：</b>'
            '<b>D14 / D19 两项角色校验缺失尚未修复</b>，工具侧的客户端闸门只防误用、不是安全控制。'
            '这也是本项目“如实标注缺口”这一安全态度的体现——'
            '能修的立刻修（搜索接口未脱敏已于 2026-10-06 修复并默认脱敏），不能修的写清楚、报上去、等回复。</p>')
sub(OLD_CONC, NEW_CONC, "结论")

io.open(DST, "w", encoding="utf-8", newline="").write(h)
print("svg 数量：改前 %d → 改后 %d（必须相等）" % (before_svg, h.count("<svg")))
print("字符数：%d → %d" % (len(io.open(SRC, encoding='utf-8').read()), len(h)))
print("成功 %d 项：" % len(done))
for d in done:
    print("   +", d)
if miss:
    print("未匹配 %d 项：" % len(miss))
    for m in miss:
        print("   !", m)
print("输出 ->", DST)