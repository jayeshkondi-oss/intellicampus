// EduCore ERP — Main JS v5
// Sidebar: FULLY HIDDEN by default, click ☰ to open/close

const sidebar  = document.getElementById('sidebar');
const mainWrap = document.querySelector('.main-wrapper');
const toggle   = document.getElementById('sidebarToggle');

const SB_FULL = '268px';
const SB_ZERO = '0px';

function applySidebar(open) {
  if (!sidebar || !mainWrap) return;
  if (open) {
    sidebar.style.transform  = 'translateX(0)';
    sidebar.style.width      = SB_FULL;
    mainWrap.style.marginLeft = SB_FULL;
    sidebar.classList.remove('collapsed');
  } else {
    sidebar.style.transform  = 'translateX(-100%)';
    mainWrap.style.marginLeft = SB_ZERO;
    sidebar.classList.add('collapsed');
  }
  localStorage.setItem('sb', open ? '1' : '0');
}

// On every page load → default CLOSED unless user explicitly opened it
const saved = localStorage.getItem('sb');
applySidebar(saved === '1');

// Toggle button
if (toggle) {
  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    const isOpen = sidebar.style.transform === 'translateX(0px)' ||
                   sidebar.style.transform === 'translateX(0)';
    applySidebar(!isOpen);
  });
}

// Click outside → close
document.addEventListener('click', function (e) {
  if (!sidebar || !toggle) return;
  const isOpen = sidebar.style.transform === 'translateX(0px)' ||
                 sidebar.style.transform === 'translateX(0)';
  if (isOpen && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
    applySidebar(false);
  }
});

// Auto-dismiss flash messages
document.querySelectorAll('.alert').forEach(function (el) {
  setTimeout(function () {
    el.style.transition = 'opacity .4s, transform .4s';
    el.style.opacity    = '0';
    el.style.transform  = 'translateY(-8px)';
    setTimeout(function () { el.remove(); }, 420);
  }, 4500);
});

// Stat count-up
document.querySelectorAll('.stat-value').forEach(function (el) {
  var raw = el.textContent.replace(/[₹,%\s,]/g, '');
  var num = parseFloat(raw);
  if (isNaN(num) || num <= 0 || num >= 10000000) return;
  var prefix = el.textContent.includes('₹') ? '₹' : '';
  var suffix = el.textContent.includes('%') ? '%' : '';
  var start  = 0, inc = num / (800 / 16);
  var timer  = setInterval(function () {
    start = Math.min(start + inc, num);
    el.textContent = prefix + (Number.isInteger(num)
      ? Math.round(start).toLocaleString('en-IN')
      : start.toFixed(1)) + suffix;
    if (start >= num) clearInterval(timer);
  }, 16);
});

// Button ripple
document.querySelectorAll('.btn').forEach(function (btn) {
  btn.addEventListener('click', function (e) {
    var r = document.createElement('span');
    var rect = this.getBoundingClientRect();
    r.style.cssText =
      'position:absolute;width:100px;height:100px;background:rgba(255,255,255,.25);' +
      'border-radius:50%;transform:translate(-50%,-50%) scale(0);' +
      'left:' + (e.clientX - rect.left) + 'px;top:' + (e.clientY - rect.top) + 'px;' +
      'animation:ripple .5s ease forwards;pointer-events:none';
    this.style.position = 'relative';
    this.style.overflow = 'hidden';
    this.appendChild(r);
    setTimeout(function () { r.remove(); }, 600);
  });
});
var s = document.createElement('style');
s.textContent = '@keyframes ripple{to{transform:translate(-50%,-50%) scale(3);opacity:0}}';
document.head.appendChild(s);
