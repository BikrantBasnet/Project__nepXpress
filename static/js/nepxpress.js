/* ═══════════════════════════════════════════════════════════════════════
   NepXpress — Main JavaScript
   ═══════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Sticky Nav ─────────────────────────────────────────────────────── */
  const nav = document.getElementById('nx-nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 40);
    }, { passive: true });
  }

  /* ── Mobile Burger ──────────────────────────────────────────────────── */
  const burger = document.getElementById('burger');
  const mobileMenu = document.getElementById('mobile-menu');
  if (burger && mobileMenu) {
    burger.addEventListener('click', () => {
      const open = mobileMenu.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
    });
  }

  /* ── Scroll Reveal ──────────────────────────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal-up, .reveal-right');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach(el => observer.observe(el));
  } else {
    // Fallback: just show everything
    revealEls.forEach(el => el.classList.add('revealed'));
  }

  /* ── Animated Counters ──────────────────────────────────────────────── */
  function animateCounter(el, target, duration) {
    let start = null;
    const startVal = 0;

    function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }

    function step(timestamp) {
      if (!start) start = timestamp;
      const elapsed = timestamp - start;
      const progress = Math.min(elapsed / duration, 1);
      const value = Math.round(easeOutQuart(progress) * target);
      el.textContent = value.toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Counter elements in the stats section (full counters)
  const counters = document.querySelectorAll('.counter');
  if ('IntersectionObserver' in window && counters.length) {
    const counterObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const target = parseInt(entry.target.dataset.target, 10);
          animateCounter(entry.target, target, 1800);
          counterObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(el => counterObs.observe(el));
  }

  // Hero inline stats (smaller counters)
  const heroCounters = document.querySelectorAll('.hero-stat__num[data-target]');
  if ('IntersectionObserver' in window && heroCounters.length) {
    const heroObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const target = parseInt(entry.target.dataset.target, 10);
          animateCounter(entry.target, target, 1400);
          heroObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    heroCounters.forEach(el => heroObs.observe(el));
  }

  /* ── Smooth Hover Parallax on Truck Card ────────────────────────────── */
  const truckCard = document.querySelector('.nx-truck-card');
  if (truckCard) {
    truckCard.addEventListener('mousemove', (e) => {
      const rect = truckCard.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width  - 0.5) * 14;
      const y = ((e.clientY - rect.top)  / rect.height - 0.5) * 10;
      truckCard.style.transform = `perspective(1000px) rotateX(${-y}deg) rotateY(${x}deg) translateZ(6px)`;
    });
    truckCard.addEventListener('mouseleave', () => {
      truckCard.style.transform = '';
    });
  }

  /* ── Feature card subtle glow on hover ──────────────────────────────── */
  document.querySelectorAll('.nx-feature').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });

  /* ── CTA button ripple ──────────────────────────────────────────────── */
  document.querySelectorAll('.btn-primary').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      ripple.style.cssText = `
        position:absolute; border-radius:50%; pointer-events:none;
        width:10px; height:10px;
        left:${e.clientX - rect.left - 5}px;
        top:${e.clientY - rect.top - 5}px;
        background:rgba(255,255,255,.4);
        transform:scale(0);
        animation:ripple .5s ease-out forwards;
      `;
      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Inject ripple keyframe
  const style = document.createElement('style');
  style.textContent = `@keyframes ripple { to { transform:scale(30); opacity:0; } }`;
  document.head.appendChild(style);

  /* ── Page load fade-in ──────────────────────────────────────────────── */
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity .4s ease';
  window.addEventListener('load', () => {
    document.body.style.opacity = '1';
  });

})();
