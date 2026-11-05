'use strict';

const slides = [...document.querySelectorAll('.slide')];
const jump = document.getElementById('jump');
const prev = document.getElementById('prev');
const next = document.getElementById('next');
let page = 1;

for (const [index, slide] of slides.entries()) {
  jump.add(new Option(`${index + 1} · ${slide.dataset.title}`, String(index + 1)));
}

function showSlide() {
  const requested = Number(location.hash.slice(1));
  page = Number.isInteger(requested) && requested > 0 && requested <= slides.length ? requested : 1;
  for (const [index, slide] of slides.entries()) slide.hidden = index !== page - 1;
  jump.value = String(page);
  prev.disabled = page === 1;
  next.disabled = page === slides.length;
  document.getElementById('counter').textContent = `${String(page).padStart(2, '0')} / ${slides.length}`;
  document.getElementById('slide-title').textContent = slides[page - 1].dataset.title;
  window.scrollTo(0, 0);
}

function go(index) {
  if (index >= 1 && index <= slides.length) location.hash = String(index);
}

prev.addEventListener('click', () => go(page - 1));
next.addEventListener('click', () => go(page + 1));
jump.addEventListener('change', () => go(Number(jump.value)));
window.addEventListener('hashchange', showSlide);
document.getElementById('print').addEventListener('click', () => window.print());
document.getElementById('fullscreen').addEventListener('click', async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  else if (document.fullscreenEnabled) await document.documentElement.requestFullscreen();
});
window.addEventListener('keydown', (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('select, input, textarea')) return;
  if (event.key === 'ArrowLeft' || event.key === 'PageUp') go(page - 1);
  else if (event.key === 'ArrowRight' || event.key === 'PageDown') go(page + 1);
  else if (event.key === 'Home') go(1);
  else if (event.key === 'End') go(slides.length);
  else return;
  event.preventDefault();
});
showSlide();
