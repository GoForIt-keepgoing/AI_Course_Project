/* Decorative illustrations stay outside forms, activities and exported materials. */
(function () {
  'use strict';
  function artwork(key, className) {
    var img = document.createElement('img');
    img.src = '/static/illustrations/' + key + '.png';
    img.alt = '';
    img.setAttribute('aria-hidden', 'true');
    img.className = 'scene-art ' + (className || '');
    img.width = 1536;
    img.height = 1024;
    img.decoding = 'async';
    img.draggable = false;
    return img;
  }
  function add(parent, key, cls) {
    if (!parent || parent.querySelector('.scene-art')) return;
    parent.appendChild(artwork(key, cls));
  }
  function decorate() {
    var root = document.documentElement;
    if (root.classList.contains('app')) {
      var login = document.querySelector('.login-left');
      if (login && !login.querySelector('.scene-art')) {
        login.insertBefore(artwork('teaching', 'login-art'), login.querySelector('.foot'));
      }
      var state = window.S || {};
      var route = state.route || [];
      var key = state.user && state.user.role !== 'teacher' ? 'learning' : 'teaching';
      if (route[0] === 'review' || /exercises|tasks|results/.test(route[2] || '')) key = 'learning';
      if (route[2] === 'activities' || route[0] === 'studio') key = 'animals';
      /* 工作区页头不放装饰插画：标题与动作需要干净的横向空间 */
    }
    if (root.classList.contains('classroom')) add(document.querySelector('.intro'), 'animals', 'classroom-art');
    if (root.classList.contains('workshop')) {
      add(document.querySelector('.hero-copy'), 'teaching', 'workshop-art');
      document.querySelectorAll('.page-heading').forEach(function (head) {
        add(head, /studio|lesson/.test(location.hash) ? 'animals' : 'teaching', 'heading-art');
      });
    }
    if (root.classList.contains('lab')) {
      add(document.querySelector('.topbar'), 'teaching', 'heading-art');
      add(document.querySelector('#view > .hero'), 'teaching', 'lab-art');
    }
    if (root.classList.contains('defense')) {
      var board = document.querySelector('.cover-grid .word-board');
      if (board && !document.querySelector('.cover-art')) {
        var group = document.createElement('div');
        group.className = 'cover-art';
        board.parentNode.insertBefore(group, board);
        group.appendChild(artwork('animals', 'defense-art'));
        group.appendChild(board);
      }
    }
  }
  var queued = false;
  var observer = new MutationObserver(function (records) {
    // Ignore our own inserts and text/input changes to avoid decoration loops.
    var changed = records.some(function (record) {
      return Array.prototype.some.call(record.addedNodes, function (node) {
        return node.nodeType === 1 && !node.classList.contains('scene-art') && !node.classList.contains('cover-art');
      });
    });
    if (!changed || queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; decorate(); });
  });
  decorate();
  observer.observe(document.body, { childList: true, subtree: true });
}());
