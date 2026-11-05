/* AI4En · 拓展工具：把工作坊与完整版的功能收进同一个外壳 */
'use strict';

var STUDIO_MODULES = [
  {
    id: 'workshop', name: '游戏工坊',
    note: '单词配对：改词卡、更新预览、课堂展示，或下载成独立 HTML 离线用。',
    src: '/static/workshop/index.html?embed=1#studio',
    raw: '/static/workshop/index.html#studio'
  },
  {
    id: 'mystery', name: '水果线索卡',
    note: '逐条揭示英文线索，让学生猜水果；沿用工作坊的水果课例词卡。',
    src: '/static/workshop/index.html?embed=1&game=mystery#studio',
    raw: '/static/workshop/index.html?game=mystery#studio'
  },
  {
    id: 'games', name: '游戏闯关',
    note: '连词成句 / 单词配对 / 记忆翻牌 / 打地鼠 / 单词跳跳岛，每局随机、限时计分。',
    src: '/static/lab/?embed=1#m6',
    raw: '/static/lab/#m6'
  },
  {
    id: 'dh', name: '数字人对话',
    note: '八个生活场景；未配置模型时是脚本对话，页面会标“演示模式”。',
    src: '/static/lab/?embed=1#m7',
    raw: '/static/lab/#m7'
  },
  {
    id: 'mindmap', name: '思维导图',
    note: '节点可拖动、增删改名，导出 SVG，用来梳理词汇与句型关系。',
    src: '/static/lab/?embed=1#mindmap',
    raw: '/static/lab/#mindmap'
  }
];

function studioModule(id) {
  for (var i = 0; i < STUDIO_MODULES.length; i++) {
    if (STUDIO_MODULES[i].id === id) return STUDIO_MODULES[i];
  }
  return STUDIO_MODULES[0];
}

function studioWithLesson(src, lesson) {
  if (!lesson) return src;
  var hash = '';
  var cut = src.indexOf('#');
  if (cut >= 0) { hash = src.slice(cut); src = src.slice(0, cut); }
  return src + (src.indexOf('?') >= 0 ? '&' : '?') + 'lesson=' + encodeURIComponent(lesson) + hash;
}

function studioView() {
  var current = studioModule((S.route && S.route[1]) || 'workshop');
  var lesson = (S.query && S.query.lesson) || '';
  var tabs = STUDIO_MODULES.map(function (m) {
    var href = '#/studio/' + m.id + (lesson ? '?lesson=' + encodeURIComponent(lesson) : '');
    return '<a href="' + href + '" class="' + (m.id === current.id ? 'active' : '') + '">' + esc(m.name) + '</a>';
  }).join('');

  return pageHead('拓展工具', '工作坊与完整版的功能都在工作台里打开，顶部导航不变；需要投屏或换设备时再从右上角新窗口打开。',
      '<a class="btn" href="#/">返回工作台</a>') +
    '<div class="tabs">' + tabs + '</div>' +
    '<div class="card" style="padding:12px">' +
      '<div class="row" style="justify-content:space-between;align-items:center;gap:12px;margin-bottom:10px">' +
        '<span class="small muted">' + esc(current.note) + '</span>' +
        '<a class="btn sm" target="_blank" rel="noopener" href="' + studioWithLesson(current.raw, lesson) + '">新窗口打开 ↗</a>' +
      '</div>' +
      '<iframe class="embed-frame" src="' + studioWithLesson(current.src, lesson) + '" title="' + esc(current.name) + '"></iframe>' +
    '</div>';
}
