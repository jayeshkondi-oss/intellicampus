// IntelliCampus ERP — Main JS v9.0
// Professional interactions and animations with gradient theme

(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // SIDEBAR FUNCTIONALITY
  // ═══════════════════════════════════════════════════════════════
  const sidebar = document.getElementById('sidebar');
  const mainWrap = document.querySelector('.main-wrapper');
  const toggle = document.getElementById('sidebarToggle');

  // Create overlay element for mobile
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  overlay.id = 'sidebarOverlay';
  document.body.appendChild(overlay);

  function openSidebar() {
    if (!sidebar) return;
    sidebar.style.transform = 'translateX(0)';
    localStorage.setItem('sb', '1');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.style.transform = 'translateX(-100%)';
    localStorage.setItem('sb', '0');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  function isOpen() {
    return sidebar && (
      sidebar.style.transform === 'translateX(0px)' ||
      sidebar.style.transform === 'translateX(0)'
    );
  }

  // Initialize: closed by default
  closeSidebar();

  // Toggle button
  if (toggle) {
    toggle.addEventListener('click', function(e) {
      e.stopPropagation();
      isOpen() ? closeSidebar() : openSidebar();
    });
  }

  // Close on nav item click
  document.querySelectorAll('.nav-item, .logout-btn').forEach(function(el) {
    el.addEventListener('click', function() {
      closeSidebar();
    });
  });

  // Close on overlay click
  overlay.addEventListener('click', closeSidebar);

  // Close on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isOpen()) closeSidebar();
  });

  // ═══════════════════════════════════════════════════════════════
  // FLASH MESSAGE AUTO-DISMISS
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('.alert').forEach(function(el) {
    setTimeout(function() {
      el.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px) scale(0.98)';
      setTimeout(function() { 
        if (el.parentNode) el.parentNode.removeChild(el); 
      }, 400);
    }, 5000);
  });

  // ═══════════════════════════════════════════════════════════════
  // STAT COUNTER ANIMATION
  // ═══════════════════════════════════════════════════════════════
  const observerOptions = {
    threshold: 0.3,
    rootMargin: '0px'
  };

  const statObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting && !entry.target.dataset.animated) {
        entry.target.dataset.animated = 'true';
        animateCounter(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.stat-value').forEach(function(el) {
    statObserver.observe(el);
  });

  function animateCounter(el) {
    const raw = el.textContent.replace(/[₹,%\s,]/g, '');
    const num = parseFloat(raw);
    if (isNaN(num) || num <= 0 || num > 9999999) return;
    
    const prefix = el.textContent.indexOf('₹') >= 0 ? '₹' : '';
    const suffix = el.textContent.indexOf('%') >= 0 ? '%' : '';
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = num * eased;
      
      el.textContent = prefix + 
        (Number.isInteger(num) 
          ? Math.round(current).toLocaleString('en-IN')
          : current.toFixed(1)) + suffix;
      
      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }
    
    requestAnimationFrame(update);
  }

  // ═══════════════════════════════════════════════════════════════
  // BUTTON RIPPLE EFFECT
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('.btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      const size = Math.max(rect.width, rect.height) * 1.5;
      
      ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%);
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        left: ${e.clientX - rect.left}px;
        top: ${e.clientY - rect.top}px;
        animation: rippleEffect 0.7s ease-out forwards;
        pointer-events: none;
      `;
      
      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);
      
      setTimeout(function() {
        if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
      }, 700);
    });
  });

  // Add ripple keyframes
  const rippleStyle = document.createElement('style');
  rippleStyle.textContent = `
    @keyframes rippleEffect {
      to {
        transform: translate(-50%, -50%) scale(2.5);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(rippleStyle);

  // ═══════════════════════════════════════════════════════════════
  // SMOOTH SCROLL FOR INTERNAL LINKS
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // FORM VALIDATION FEEDBACK
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('.form-control').forEach(function(input) {
    input.addEventListener('invalid', function(e) {
      this.classList.add('error');
    });
    
    input.addEventListener('input', function() {
      this.classList.remove('error');
    });

    // Add focus glow effect
    input.addEventListener('focus', function() {
      this.parentElement?.classList?.add('input-focused');
    });
    
    input.addEventListener('blur', function() {
      this.parentElement?.classList?.remove('input-focused');
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // TABLE ROW HOVER ENHANCEMENT
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('tbody tr').forEach(function(row) {
    row.addEventListener('mouseenter', function() {
      this.style.transition = 'all 0.2s ease';
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // CARD TILT EFFECT (enhanced)
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('.stat-card, .quick-card').forEach(function(card) {
    card.addEventListener('mousemove', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = (y - centerY) / 25;
      const rotateY = (centerX - x) / 25;
      
      this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px) scale(1.02)`;
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = '';
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // PROGRESS BAR ANIMATION
  // ═══════════════════════════════════════════════════════════════
  const progressObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting && !entry.target.dataset.animated) {
        entry.target.dataset.animated = 'true';
        const width = entry.target.style.width;
        entry.target.style.width = '0';
        requestAnimationFrame(function() {
          entry.target.style.transition = 'width 1s cubic-bezier(0.4, 0, 0.2, 1)';
          entry.target.style.width = width;
        });
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.progress-bar, .progress-fill').forEach(function(el) {
    progressObserver.observe(el);
  });

  // ═══════════════════════════════════════════════════════════════
  // KEYBOARD NAVIGATION
  // ═══════════════════════════════════════════════════════════════
  document.addEventListener('keydown', function(e) {
    // Focus search on Ctrl/Cmd + K
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const search = document.querySelector('.topbar-search input');
      if (search) search.focus();
    }
    
    // Toggle sidebar on Ctrl/Cmd + B
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
      e.preventDefault();
      isOpen() ? closeSidebar() : openSidebar();
    }
  });

  // ═══════════════════════════════════════════════════════════════
  // TOOLTIP INITIALIZATION
  // ═══════════════════════════════════════════════════════════════
  document.querySelectorAll('[data-tooltip]').forEach(function(el) {
    el.addEventListener('mouseenter', function() {
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.textContent = this.dataset.tooltip;
      tooltip.style.cssText = `
        position: absolute;
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: #fff;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        white-space: nowrap;
        z-index: 1000;
        opacity: 0;
        transform: translateY(-6px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: none;
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.3);
      `;
      
      document.body.appendChild(tooltip);
      
      const rect = this.getBoundingClientRect();
      tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
      tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
      
      requestAnimationFrame(function() {
        tooltip.style.opacity = '1';
        tooltip.style.transform = 'translateY(0)';
      });
      
      this._tooltip = tooltip;
    });
    
    el.addEventListener('mouseleave', function() {
      if (this._tooltip) {
        this._tooltip.remove();
        this._tooltip = null;
      }
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // GRADIENT BACKGROUND MOUSE FOLLOW (subtle)
  // ═══════════════════════════════════════════════════════════════
  let lastX = 0, lastY = 0;
  document.addEventListener('mousemove', function(e) {
    // Throttle to improve performance
    if (Math.abs(e.clientX - lastX) < 50 && Math.abs(e.clientY - lastY) < 50) return;
    lastX = e.clientX;
    lastY = e.clientY;
    
    const x = (e.clientX / window.innerWidth) * 100;
    const y = (e.clientY / window.innerHeight) * 100;
    
    document.body.style.setProperty('--mouse-x', x + '%');
    document.body.style.setProperty('--mouse-y', y + '%');
  });

  // ═══════════════════════════════════════════════════════════════
  // PAGE LOAD ANIMATION
  // ═══════════════════════════════════════════════════════════════
  document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('loaded');
    
    // Stagger fade-in animations
    document.querySelectorAll('.fade-in').forEach(function(el, i) {
      el.style.animationDelay = (i * 0.05) + 's';
    });
  });

  console.log('✨ IntelliCampus ERP v9.0 initialized');

})();
