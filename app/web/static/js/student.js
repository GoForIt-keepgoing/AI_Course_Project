/* AI4En · 学生端与家长端 */
'use strict';

/* ---------------------------------------------------------------- 学生首页 */
function studentHomeView(tasks) {
  var cards = tasks.map(function (t) {
    var sub = t.submission;
    var status = sub ? sub.status : (t.status === 'ended' ? 'ended' : 'open');
    var chipHtml = sub ? subChip(sub.status) : (t.status === 'ended' ? chip('已结束 · 未提交', 'red') : chip('未提交', 'amber'));
    return '<div class="card lesson-card ' + (sub ? '' : 'draft') + '"><div class="top"><div><h3>' + esc(t.title) + '</h3>' +
      '<div class="meta">' + esc(t.lesson_title) + ' · ' + t.item_count + ' 题</div></div>' + chipHtml + '</div>' +
      '<div class="meta"><span>截止 ' + esc(t.due_at || '不限') + '</span>' +
      (sub ? '<span>提交于 ' + esc(String(sub.submitted_at).slice(0, 16)) + '</span>' : '<span>还没有提交</span>') + '</div>' +
      '<div class="row"><a class="btn primary sm" href="#/student/task/' + t.id + '">' +
      (sub ? (sub.status === 'revision_requested' ? '去订正' : '查看作业与反馈') : '开始作答') + '</a></div></div>';
  }).join('');
  return pageHead('我的任务', esc(S.user.name) + ' · ' + esc(S.user.class_name || '') + ' · 共 ' + tasks.length + ' 个任务', '') +
    banner('你只会看到自己班的任务与自己的作答。老师的标准答案和其他同学的记录不会出现在这里。', 'info', 'i') +
    '<div class="grid two" style="margin-top:16px">' + (cards || empty('暂时没有任务。')) + '</div>';
}

/* ---------------------------------------------------------------- 学生任务页 */
async function studentTaskView(id) {
  var data = await api('/api/tasks/' + id + '/student');
  S.stTask = data;
  var task = data.task;
  var sub = data.submission;
  var items = data.items || [];

  if (!sub) {
    S.answers = S.answers && S.answerTaskId === id ? S.answers : {};
    S.answerTaskId = id;
    return studentHeader(task, '') + studentForm(task, items, false);
  }
  S.answers = S.answerTaskId === id ? S.answers : clone(sub.answers || {});
  S.answerTaskId = id;

  var feedback = sub.feedback || {};
  var grading = sub.grading || {};
  var answered = Object.keys(sub.answers || {}).length;
  var correct = Object.keys(grading).filter(function (k) { return grading[k] === true; }).length;
  var totalObj = Object.keys(grading).length;

  var summary = '<div class="grid stats" style="margin-bottom:16px">' +
    '<div class="stat teal"><div class="num">' + subChip(sub.status) + '</div><div class="label">提交状态</div>' +
    '<div class="extra">提交于 ' + esc(String(sub.submitted_at).slice(0, 16)) + '</div></div>' +
    '<div class="stat"><div class="num">' + answered + ' / ' + items.length + '</div><div class="label">已作答</div>' +
    '<div class="extra">提交后不能修改，除非老师要求订正</div></div>' +
    '<div class="stat"><div class="num">' + (sub.reveal_result ? correct + ' / ' + totalObj : '—') + '</div><div class="label">客观题正确</div>' +
    '<div class="extra">' + (sub.reveal_result ? '按老师确认的答案判定' : '老师设置了稍后展示') + '</div></div>' +
    '<div class="stat"><div class="num">' + Object.keys(feedback).length + '</div><div class="label">已确认反馈</div>' +
    '<div class="extra">只有老师确认后才会显示</div></div></div>';

  var itemHtml = items.map(function (item, i) {
    var ans = (sub.answers || {})[item.id];
    var ok = grading[item.id];
    var fb = feedback[item.id];
    var body = '';
    if (item.type === 'choice') {
      body = '<div class="opt-list">' + (item.options || []).map(function (o, j) {
        var letter = String.fromCharCode(65 + j);
        var cls = 'opt-row';
        if (sub.reveal_result && ans === letter) cls += ok ? ' correct' : ' wrong';
        else if (sub.reveal_result && item.answer === letter && ans !== letter) cls += ' correct';
        return '<div class="' + cls + '"><span class="opt-key">' + letter + '</span><span>' + esc(o) + '</span>' +
          (ans === letter ? '<span class="chip plain" style="margin-left:auto">你的选择</span>' : '') + '</div>';
      }).join('') + '</div>';
    } else {
      body = '<div class="answer-line" style="margin-left:36px"><span class="tiny muted">你的作答：</span>' +
        '<div>' + (ans ? esc(ans) : '<span class="muted">未作答</span>') + '</div></div>';
    }
    return '<div class="card" style="margin-bottom:12px"><div class="q-head" style="display:flex;gap:10px;align-items:baseline">' +
      '<span class="q-no">' + (i + 1) + '</span><span class="q-stem">' + esc(item.stem) + '</span>' +
      (sub.reveal_result && item.type !== 'short'
        ? '<span class="q-meta">' + (ok === true ? chip('正确', 'teal') : ok === false ? chip('再检查', 'red') : '') + '</span>' : '') +
      '</div>' + body +
      (fb ? '<div class="feedback-box"><div class="fb-head">老师已确认的反馈 ' + levelChip(fb.level) + '</div>' + nl2br(fb.final) + '</div>' : '') +
      '</div>';
  }).join('');

  var reviseBanner = sub.can_revise
    ? '<div class="card revise-banner" style="margin-bottom:16px"><div class="row" style="justify-content:space-between">' +
      '<div><b>老师要求订正</b><div class="small muted">读完老师的反馈再改；提交后首次作答仍会保留。</div></div>' +
      btn(S.revising ? '收起订正' : '开始订正', 'toggle-revise', '', 'primary') + '</div></div>' +
      (S.revising ? studentForm(task, items, true) : '')
    : '';

  return studentHeader(task, '<a class="btn" href="#/student">返回任务列表</a>') +
    summary + itemHtml + reviseBanner;
}

function studentHeader(task, actions) {
  var ruleText = [];
  ruleText.push(task.allow_hints ? '本次可以点“提示”' : '本次不提供提示');
  if (task.show_result === 'immediately') ruleText.push('提交后立即显示客观题对错');
  else if (task.show_result === 'after_end') ruleText.push('任务结束后显示对错');
  else ruleText.push('不显示对错，只显示已提交');
  return '<div class="page-head"><div><div class="tiny muted"><a href="#/student">我的任务</a> / 作业</div>' +
    '<h1>' + esc(task.title) + '</h1>' +
    '<div class="sub">' + esc(task.instructions || '') + '</div></div><div class="row">' + (actions || '') + '</div></div>' +
    '<div class="row" style="margin-bottom:14px">' + chip('截止 ' + (task.due_at || '不限'), 'plain') + chip(ruleText.join(' · '), 'gray') +
    (task.status === 'ended' ? chip('任务已结束', 'gray') : '') +
    (task.overdue && task.status !== 'ended' ? chip('已过提交时间', 'red') : '') + '</div>';
}

function studentForm(task, items, revising) {
  var editable = revising ? true : (task.status === 'ongoing' && !task.overdue);
  var rows = items.map(function (item, i) {
    var ans = (S.answers || {})[item.id] || '';
    var input = '';
    if (item.type === 'choice') {
      input = '<div class="opt-list">' + (item.options || []).map(function (o, j) {
        var letter = String.fromCharCode(65 + j);
        return '<label class="opt-row' + (ans === letter ? ' selected' : '') + '">' +
          '<input type="radio" name="ans-' + item.id + '" value="' + letter + '" data-state="answers" data-bind="' + item.id + '"' +
          (ans === letter ? ' checked' : '') + (editable ? '' : ' disabled') + '>' +
          '<span class="opt-key">' + letter + '</span><span>' + esc(o) + '</span></label>';
      }).join('') + '</div>';
    } else if (item.type === 'fill') {
      input = '<div class="answer-line"><input class="input" data-state="answers" data-bind="' + item.id + '" value="' + esc(ans) + '"' +
        (editable ? '' : ' disabled') + ' placeholder="填写一个单词"></div>';
    } else {
      var support = '';
      if (S.stTask && S.stTask.items) {
        var extra = item.frame ? '<div class="tiny muted">句架：' + esc(item.frame) + '</div>' : '';
        var kw = item.keywords ? '<div class="tiny muted">关键词：' + esc(item.keywords) + '</div>' : '';
        support = extra + kw;
      }
      input = '<div style="margin-left:36px">' + support +
        '<textarea class="textarea" rows="4" style="margin-top:8px" data-state="answers" data-bind="' + item.id + '"' +
        (editable ? '' : ' disabled') + ' placeholder="写 2 句话">' + esc(ans) + '</textarea></div>';
    }
    return '<div class="q-item"><div class="q-head"><span class="q-no">' + (i + 1) + '</span>' +
      '<span class="q-stem">' + esc(item.stem) + '</span><span class="q-meta">' + (TYPE_LABEL[item.type] || '') + '</span></div>' +
      input +
      (task.allow_hints && item.hint && editable
        ? '<div style="margin:8px 0 0 36px"><button class="btn sm ghost" data-act="show-hint" data-item="' + item.id + '">提示</button>' +
          '<span class="tiny muted" id="hint-' + item.id + '" style="display:none">' + esc(item.hint) + '</span></div>' : '') +
      '</div>';
  }).join('');

  var overdueNote = (!revising && task.overdue)
    ? banner('已超过提交时间（' + esc(task.due_at) + '），本次不能提交。请联系老师说明情况，由老师决定是否补交。', 'warn', '!')
    : '';

  return overdueNote + '<div class="card pad-lg"><div class="section-title"><span class="dot"></span>' +
    (revising ? '订正作答' : '作答') + '</div>' +
    '<div class="card-sub">共 ' + items.length + ' 题。提交前请确认每题都已作答，未作答的题目不会提交成功。</div>' +
    '<div id="answerForm">' + rows + '</div>' +
    '<div class="row" style="margin-top:18px;justify-content:space-between">' +
    '<span class="tiny muted">提交后页面会显示客观题结果与老师已确认的反馈。</span>' +
    (revising ? btn('提交订正', 'submit-revise', 'data-sid="' + (S.stTask && S.stTask.submission ? S.stTask.submission.id : '') + '"', 'primary')
              : (task.overdue ? btn('已过提交时间', 'submit-task', 'disabled', 'primary') : btn('提交作业', 'submit-task', 'data-id="' + task.id + '"', 'primary'))) +
    '</div></div>';
}

ACTIONS['show-hint'] = function (el) {
  var hint = document.getElementById('hint-' + el.getAttribute('data-item'));
  if (hint) hint.style.display = hint.style.display === 'none' ? 'inline' : 'none';
};

ACTIONS['toggle-revise'] = function () {
  S.revising = !S.revising;
  render();
};

ACTIONS['submit-task'] = async function (el) {
  var id = el.getAttribute('data-id');
  var res = await api('/api/tasks/' + id + '/submit', 'POST', { answers: S.answers });
  toast(res.notice || '已提交', 'ok');
  S.answerTaskId = null;
  await render();
};

ACTIONS['submit-revise'] = async function (el) {
  var sid = el.getAttribute('data-sid');
  var res = await api('/api/submissions/' + sid + '/revise', 'POST', { answers: S.answers });
  toast(res.notice || '订正已提交', 'ok');
  S.revising = false;
  S.answerTaskId = null;
  await render();
};

/* ---------------------------------------------------------------- 家长端 */
function parentHomeView(data) {
  var child = data.child || {};
  var cards = (data.tasks || []).map(function (t) {
    var sub = t.submission;
    var statusChip = sub ? subChip(sub.status) : chip('未提交', 'amber');
    var fb = (t.feedback || []).map(function (f) {
      return '<div class="feedback-box" style="margin-left:0"><div class="fb-head">老师反馈 ' + levelChip(f.level) + '</div>' +
        '<div class="tiny muted" style="margin-bottom:4px">' + esc(f.stem) + '</div>' + nl2br(f.final) + '</div>';
    }).join('');
    return '<div class="card lesson-card"><div class="top"><div><h3>' + esc(t.title) + '</h3>' +
      '<div class="meta">' + esc(t.lesson_title) + ' · 截止 ' + esc(t.due_at || '不限') + '</div></div>' + statusChip + '</div>' +
      (sub ? '<div class="tiny muted">提交于 ' + esc(String(sub.submitted_at).slice(0, 16)) + '</div>' : '') +
      fb +
      '<div class="banner info" style="margin-top:12px"><span class="icon">i</span><div><b>陪伴建议</b><br>' + esc(t.suggestion) + '</div></div>' +
      '</div>';
  }).join('');
  return pageHead('孩子任务', '家长视角 · 只读 · 只显示绑定孩子的内容', '') +
    '<div class="card" style="margin-bottom:16px"><div class="row" style="justify-content:space-between">' +
    '<div><div class="tiny muted">我的孩子</div><h3>' + esc(child.name || '') + '</h3></div>' +
    '<div class="row">' + chip('只读', 'gray') + chip('不含答案与排名', 'plain') + '</div></div></div>' +
    banner('这里只显示孩子的任务说明、提交与订正状态、老师已确认的反馈。看不到标准答案、其他孩子记录或班级排名。', 'info', 'i') +
    '<div class="grid two" style="margin-top:16px">' + (cards || empty('暂时没有可查看的任务。')) + '</div>';
}
