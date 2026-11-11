/* AI4En · 前端核心：状态、接口、路由、外壳、登录 */
'use strict';

var S = {
  user: null,
  route: [],
  lesson: null, plan: null, slides: [], slideIdx: 0, ex: null,
  tasks: [], results: null, resultTaskId: null,
  taskForm: null, cond: null, answers: {}, review: null,
  guideTab: 'steps', modal: null, notice: null, busy: false
};
var META = { accounts: [], levels: ['已完成', '需局部修改', '需教师帮助'], sources: {}, guide: null, show_result_options: [] };
var SOURCE_LABEL = { model: '真实模型输出', sample: '示例内容', rule: '规则生成', manual: '教师手工编辑' };
var SUB_LABEL = { submitted: '已提交', revision_requested: '待订正', resubmitted: '已订正' };
var TASK_LABEL = { draft: '草稿', ongoing: '进行中', ended: '已结束' };
var LESSON_LABEL = { draft: '草稿', approved: '已审核' };
var LEVEL_CLASS = { '已完成': 'teal', '需局部修改': 'amber', '需教师帮助': 'red' };

/* ---------------------------------------------------------------- 基础工具 */
function q(sel, root) { return (root || document).querySelector(sel); }
function qa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
function esc(value) {
  return String(value === undefined || value === null ? '' : value).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
function clone(obj) { return JSON.parse(JSON.stringify(obj === undefined ? null : obj)); }
function setPath(obj, path, val) {
  var parts = String(path).split('.');
  var cur = obj;
  for (var i = 0; i < parts.length - 1; i++) {
    var k = parts[i];
    if (cur[k] === undefined || cur[k] === null) cur[k] = /^\d+$/.test(parts[i + 1]) ? [] : {};
    cur = cur[k];
  }
  cur[parts[parts.length - 1]] = val;
}
function getPath(obj, path) {
  return String(path).split('.').reduce(function (o, k) { return o === undefined || o === null ? undefined : o[k]; }, obj);
}
function nl2br(text) { return esc(text).replace(/\n/g, '<br>'); }
function num(value) { return (value === null || value === undefined || value === '') ? '—' : value; }

async function api(path, method, body) {
  var opts = { method: method || 'GET', credentials: 'same-origin', headers: {} };
  if (body !== undefined && body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  var res = await fetch(path, opts);
  var data = null;
  try { data = await res.json(); } catch (e) { data = { error: '返回内容无法解析' }; }
  if (!res.ok) {
    var err = new Error(data && data.error ? data.error : '请求失败（' + res.status + '）');
    err.status = res.status;
    err.data = data || {};
    throw err;
  }
  if (opts.method !== 'GET' && S.user && S.user.role === 'teacher' && typeof TW !== 'undefined') TW.mutations = (TW.mutations || 0) + 1;
  return data;
}

function toast(message, kind) {
  var box = document.getElementById('toast');
  if (!box) return;
  var el = document.createElement('div');
  el.className = 'toast ' + (kind || '');
  el.textContent = message;
  box.appendChild(el);
  setTimeout(function () { el.remove(); }, kind === 'error' ? 6000 : 3600);
}

function fail(err) {
  if (err && err.status === 401) {
    S.user = null;
    render();
    return;
  }
  var extra = err && err.data && err.data.missing ? '（缺失：' + err.data.missing.join('；') + '）' : '';
  toast((err && err.message ? err.message : '操作失败') + extra, 'error');
}

/* ---------------------------------------------------------------- 片段 */
function btn(label, act, attrs, cls) {
  return '<button class="btn ' + (cls || '') + '" data-act="' + act + '" ' + (attrs || '') + '>' + label + '</button>';
}
function link(label, href, cls) {
  return '<a class="btn ' + (cls || '') + '" href="' + href + '" target="_blank" rel="noopener">' + label + '</a>';
}
function chip(text, kind) { return '<span class="chip ' + (kind || '') + '">' + esc(text) + '</span>'; }
function srcBadge(source) {
  var label = SOURCE_LABEL[source] || source || '未标注';
  var cls = source === 'sample' ? 'sample' : source === 'manual' ? 'manual' : source === 'model' ? 'model' : '';
  return '<span class="badge-src ' + cls + '">' + esc(label) + '</span>';
}
function lessonChip(status) { return chip(LESSON_LABEL[status] || status, status === 'approved' ? 'teal' : 'amber'); }
function taskChip(status) { return chip(TASK_LABEL[status] || status, status === 'ongoing' ? 'teal' : status === 'draft' ? 'amber' : 'gray'); }
function subChip(status) { return chip(SUB_LABEL[status] || status, status === 'resubmitted' ? 'teal' : status === 'revision_requested' ? 'amber' : 'gray'); }
function levelChip(level) {
  if (!level) return '';
  return chip(level, LEVEL_CLASS[level] || 'gray');
}
function pageHead(title, sub, actions) {
  return '<div class="page-head"><div><h1>' + title + '</h1>' +
    (sub ? '<div class="sub">' + sub + '</div>' : '') + '</div>' +
    '<div class="row">' + (actions || '') + '</div></div>';
}
function banner(text, kind, icon) {
  return '<div class="banner ' + (kind || 'info') + '"><span class="icon">' + (icon || '·') + '</span><div>' + text + '</div></div>';
}
function empty(text) { return '<div class="card" style="text-align:center;color:#5b6b73;padding:34px">' + esc(text) + '</div>'; }

/* ---------------------------------------------------------------- 外壳 */
function roleLabel(role) {
  return role === 'teacher' ? '教师' : role === 'student' ? '学生' : '家长';
}

function pageMeta() {
  if (S.user.role === 'teacher' && typeof teacherPageMeta === 'function') return teacherPageMeta();
  var role = S.user.role;
  var segs = S.route || [];
  var first = segs[0] || '';
  if (first === 'lesson') {
    var tabs = { plan: '教案备课', slides: '课件资源', activities: '课堂活动', exercises: '练习与小测', tasks: '任务发布', results: '结果与日志' };
    return { title: '课例', sub: tabs[segs[2]] || '课例详情' };
  }
  if (first === 'review') return { title: '课例', sub: '批改与订正' };
  if (first === 'studio') return { title: '工具', sub: '拓展：工作坊与完整版' };
  if (first === 'guide') return { title: '帮助', sub: '使用指南与培训' };
  if (role === 'teacher') return { title: '工作台', sub: (S.user.class_name || '') + ' · 全部课例' };
  if (role === 'student') return { title: '学习', sub: segs[1] === 'task' ? '作业作答' : '我的任务与订正' };
  return { title: '孩子', sub: '只读查看任务与已确认反馈' };
}

function shellNav() {
  if (S.user.role === 'teacher' && typeof teacherNav === 'function') return teacherNav();
  var role = S.user.role;
  var first = (S.route || [])[0] || '';
  var items = [];
  if (role === 'teacher') {
    items.push(['group', '总览']);
    items.push(['#/', '🏠', '工作台', first === '' || first === 'lesson' || first === 'review']);
    items.push(['group', '工具']);
    items.push(['#/studio', '🧩', '拓展', first === 'studio']);
    items.push(['#/guide', '📘', '使用指南', first === 'guide']);
  } else if (role === 'student') {
    items.push(['group', '学习']);
    items.push(['#/', '📝', '我的任务', true]);
  } else {
    items.push(['group', '孩子']);
    items.push(['#/', '👪', '孩子任务', true]);
  }
  return items.map(function (it) {
    if (it[0] === 'group') return '<div class="side-group">' + esc(it[1]) + '</div>';
    return '<a href="' + it[0] + '" class="' + (it[3] ? 'active' : '') + '"><span class="ico">' + it[1] + '</span>' + esc(it[2]) + '</a>';
  }).join('');
}

function shell(content) {
  var role = S.user.role;
  var meta = pageMeta();
  var foot = role === 'teacher' ? '教师主导 · 内容可编辑 · 结果可核对'
    : role === 'student' ? '提交后由老师确认反馈，可完成一次订正'
      : '只读 · 仅显示本人孩子的任务与已确认反馈';
  return '<div class="shell shell-' + role + '"><aside class="side">' +
      '<a class="side-brand" href="#/"><span class="logo">AI4En</span><span class="sub">英语教学助手</span></a>' +
      '<nav class="side-nav">' + shellNav() + '</nav>' +
      '<div class="side-foot">' + esc(foot) + '</div></aside>' +
      '<div class="main"><header class="topbar">' +
        '<div class="top-title"><div class="t">' + esc(meta.title) + '</div><p>' + esc(meta.sub) + '</p></div>' +
        '<div class="top-actions"><span class="role-chip">' + roleLabel(role) + '</span>' +
        '<span class="who-name">' + esc(S.user.name) + '</span>' +
        '<button class="btn sm ghost" data-act="logout">退出</button></div>' +
      '</header>' + (role === 'teacher' && typeof teacherContext === 'function' ? teacherContext() : '') +
      '<main class="content"><div class="container">' + content + '</div></main></div></div>';
}

function modal(html) {
  var mask = document.createElement('div');
  mask.className = 'modal-mask';
  mask.id = 'modal';
  mask.innerHTML = html;
  mask.addEventListener('click', function (e) { if (e.target === mask) closeModal(); });
  document.body.appendChild(mask);
  return mask;
}
function closeModal() {
  var el = document.getElementById('modal');
  if (el) el.remove();
}

/* ---------------------------------------------------------------- 视图调度 */
async function render() {
  if (S.user && S.user.role === 'teacher' && typeof teacherBeforeRender === 'function' && !teacherBeforeRender()) return;
  var app = document.getElementById('app');
  if (!S.user) {
    app.innerHTML = typeof loginView === 'function' ? loginView() : '<div class="container">加载中…</div>';
    if (typeof afterRender === 'function') afterRender();
    return;
  }
  var rawHash = location.hash.replace(/^#\/?/, '');
  var query = {};
  var qAt = rawHash.indexOf('?');
  if (qAt >= 0) {
    rawHash.slice(qAt + 1).split('&').forEach(function (pair) {
      var kv = pair.split('=');
      if (kv[0]) query[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1] || '');
    });
    rawHash = rawHash.slice(0, qAt);
  }
  var segs = rawHash.split('/').filter(Boolean);
  S.route = segs;
  S.query = query;
  var main = '';
  try {
    if (S.user.role === 'teacher' && typeof teacherWorkspaceView === 'function') main = await teacherWorkspaceView(segs);
    else if (segs[0] === 'lesson') main = await lessonView(parseInt(segs[1], 10), segs[2] || 'plan');
    else if (segs[0] === 'review') main = await reviewView(parseInt(segs[1], 10));
    else if (segs[0] === 'student' && segs[1] === 'task') main = await studentTaskView(parseInt(segs[2], 10));
    else if (segs[0] === 'studio') main = studioView();
    else if (segs[0] === 'guide') main = guideView();
    else main = await homeView();
  } catch (err) {
    if (err && err.status === 401) { S.user = null; return render(); }
    main = '<div class="card pad-lg">' + banner(esc(err.message || '页面加载失败'), 'error', '!') +
      '<div class="row" style="margin-top:14px"><a class="btn" href="#/">返回首页</a></div></div>';
  }
  app.innerHTML = shell(main);
  if (typeof afterRender === 'function') afterRender();
  if (S.user.role === 'teacher' && typeof teacherAfterRender === 'function') teacherAfterRender();
}

async function homeView() {
  if (S.user.role === 'teacher') {
    var data = await api('/api/lessons');
    return teacherHomeView(data.lessons);
  }
  if (S.user.role === 'student') {
    var mine = await api('/api/my/tasks');
    return studentHomeView(mine.tasks);
  }
  var parent = await api('/api/parent/overview');
  return parentHomeView(parent);
}

/* ---------------------------------------------------------------- 登录 */
function loginView() {
  var accounts = (META.accounts || []).map(function (a) {
    return '<div class="demo-row" data-act="fill-login" data-u="' + esc(a.username) + '" data-p="' + esc(a.password) + '">' +
      '<span class="r">' + esc(a.role) + '</span><span class="u">' + esc(a.username) + '</span>' +
      '<span class="pw">/ ' + esc(a.password) + '</span><span class="n">' + esc(a.note) + '</span></div>';
  }).join('');
  return '<div class="login-wrap"><div class="login-left">' +
    '<div><div class="brandline">AI4En · 英语教学助手</div>' +
    '<div class="lead">从备课到反馈的一条教学链路：一份课例同时生成教案、课件、课堂活动与练习，' +
    '学生作答后由教师确认反馈，再完成订正与教学日志。</div>' +
    '<div class="flow-chips"><span>新建课例</span><span>教案</span><span>课件</span><span>课堂活动</span>' +
    '<span>练习与小测</span><span>发布</span><span>提交</span><span>反馈</span><span>订正</span><span>复盘</span></div>' +
    '<div class="login-points">' +
    '<div class="p"><b>教师</b>生成可编辑的教案、课件与练习，发布前逐项核对。</div>' +
    '<div class="p"><b>学生</b>看到本人任务，提交后按教师确认的反馈订正。</div>' +
    '<div class="p"><b>家长</b>只读绑定孩子的任务状态与已确认反馈。</div>' +
    '</div></div><div class="foot">教师主导 · 内容可编辑 · 结果可核对</div></div>' +
    '<div class="login-right"><div class="login-form">' +
    '<h2>登录</h2><div class="sub muted small" style="margin-bottom:18px">使用预置的演示账号进入对应视角</div>' +
    '<form id="loginForm" class="form-grid">' +
    '<div class="field"><label>账号</label><input class="input" id="username" value="t_wang" autocomplete="username"></div>' +
    '<div class="field"><label>密码</label><input class="input" id="password" type="password" value="teach123" autocomplete="current-password"></div>' +
    '<button class="btn primary lg block" type="submit" data-act="login">进入工作台</button>' +
    '</form>' +
    '<div class="demo-table"><div class="tiny muted" style="margin-bottom:6px">演示账号（点击填入）</div>' + accounts + '</div>' +
    '</div></div></div>';
}

async function doLogin() {
  var username = q('#username').value.trim();
  var password = q('#password').value;
  try {
    var res = await api('/api/login', 'POST', { username: username, password: password });
    S.user = res.user;
    S.lesson = null; S.plan = null; S.ex = null; S.slides = [];
    location.hash = '#/';
    await render();
  } catch (err) {
    fail(err);
  }
}

/* ---------------------------------------------------------------- 事件总线 */
var ACTIONS = {};

document.addEventListener('click', function (e) {
  var target = e.target.closest('[data-act]');
  if (!target) return;
  if (target.tagName === 'SELECT') return;
  var act = target.getAttribute('data-act');
  var fn = ACTIONS[act];
  if (!fn) return;
  e.preventDefault();
  Promise.resolve(fn(target)).catch(fail);
});

document.addEventListener('submit', function (e) {
  if (e.target.id === 'loginForm') {
    e.preventDefault();
    Promise.resolve(doLogin()).catch(fail);
  }
});

function bindState(name) {
  if (name === 'plan') return S.plan;
  if (name === 'ex') return S.ex;
  if (name === 'slides') return S.slides;
  if (name === 'taskForm') return S.taskForm;
  if (name === 'cond') return S.cond;
  if (name === 'answers') return S.answers;
  if (name === 'review') return S.review;
  if (name === 'logForm') return S.logForm;
  return S;
}

document.addEventListener('input', function (e) {
  var node = e.target.closest('[data-bind]');
  if (!node) return;
  var state = bindState(node.getAttribute('data-state'));
  if (!state) return;
  var value = node.type === 'checkbox' ? node.checked : node.value;
  setPath(state, node.getAttribute('data-bind'), value);
});

document.addEventListener('change', function (e) {
  if (e.target.matches('select[data-act]') && ACTIONS[e.target.dataset.act]) {
    Promise.resolve(ACTIONS[e.target.dataset.act](e.target)).catch(fail);
  }
  var node = e.target.closest('[data-bind]');
  if (node) {
    var state = bindState(node.getAttribute('data-state'));
    if (state) setPath(state, node.getAttribute('data-bind'), node.type === 'checkbox' ? node.checked : node.value);
  }
  var radio = e.target.closest('input[type=radio][data-bind]');
  if (radio) {
    qa('.opt-row', radio.closest('.opt-list')).forEach(function (row) { row.classList.remove('selected'); });
    var row = radio.closest('.opt-row');
    if (row) row.classList.add('selected');
  }
});

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    var overlay = document.getElementById('present');
    if (overlay) { overlay.remove(); return; }
    closeModal();
  }
});

ACTIONS.logout = async function () {
  try { await api('/api/logout', 'POST', {}); } catch (e) { /* 忽略 */ }
  S.user = null;
  location.hash = '#/';
  render();
};

ACTIONS['fill-login'] = function (el) {
  q('#username').value = el.getAttribute('data-u');
  q('#password').value = el.getAttribute('data-p');
};
