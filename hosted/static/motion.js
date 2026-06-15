/* Talent-Augmenting OS: motion + interaction layer.
   Vanilla, dependency-free. Everything self-gates:
   - heavy motion (mesh, cursor glow, parallax) only runs on marketing
     pages (body.marketing) and respects prefers-reduced-motion;
   - UI helpers (tabs, copy, carousel, accordion, mobile nav) run
     wherever they find their data-* hooks.
   Loaded on every page via base.html, but does nothing without hooks. */
(function () {
  'use strict';

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isMarketing = document.body && document.body.classList.contains('marketing');

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  // ── Scroll reveal ──────────────────────────────────────────────────────
  function initReveal() {
    var els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;
    if (reduce || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var delay = el.getAttribute('data-reveal-delay');
        if (delay) el.style.transitionDelay = delay + 'ms';
        el.classList.add('is-visible');
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  // ── Count up ───────────────────────────────────────────────────────────
  function initCountUp() {
    var els = document.querySelectorAll('[data-countup]');
    if (!els.length) return;
    function run(el) {
      var target = parseFloat(el.getAttribute('data-countup'));
      var dec = parseInt(el.getAttribute('data-decimals') || '0', 10);
      var prefix = el.getAttribute('data-prefix') || '';
      var suffix = el.getAttribute('data-suffix') || '';
      if (isNaN(target)) return;
      if (reduce) { el.textContent = prefix + target.toFixed(dec) + suffix; return; }
      var dur = 1400, start = null;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min(1, (ts - start) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = prefix + (target * eased).toFixed(dec) + suffix;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    if (!('IntersectionObserver' in window)) { els.forEach(run); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { run(e.target); io.unobserve(e.target); }
      });
    }, { threshold: 0.5 });
    els.forEach(function (el) { io.observe(el); });
  }

  // ── Cursor glow (marketing only) ─────────────────────────────────────────
  function initCursorGlow() {
    if (!isMarketing || reduce) return;
    var glow = document.querySelector('.cursor-glow');
    if (!glow || !window.matchMedia('(pointer: fine)').matches) return;
    var x = window.innerWidth / 2, y = window.innerHeight / 3, tx = x, ty = y, raf = null;
    function loop() {
      x += (tx - x) * 0.12; y += (ty - y) * 0.12;
      glow.style.transform = 'translate(' + x + 'px,' + y + 'px) translate(-50%, -50%)';
      if (Math.abs(tx - x) > 0.5 || Math.abs(ty - y) > 0.5) raf = requestAnimationFrame(loop);
      else raf = null;
    }
    window.addEventListener('pointermove', function (e) {
      tx = e.clientX; ty = e.clientY;
      if (!raf) raf = requestAnimationFrame(loop);
    }, { passive: true });
    glow.classList.add('is-on');
  }

  // ── Parallax ─────────────────────────────────────────────────────────────
  function initParallax() {
    if (reduce) return;
    var els = document.querySelectorAll('[data-parallax]');
    if (!els.length) return;
    var ticking = false;
    function update() {
      var vh = window.innerHeight;
      els.forEach(function (el) {
        var speed = parseFloat(el.getAttribute('data-parallax')) || 0.15;
        var r = el.getBoundingClientRect();
        var center = r.top + r.height / 2 - vh / 2;
        el.style.transform = 'translate3d(0,' + (-center * speed).toFixed(1) + 'px,0)';
      });
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  // ── Animated gradient-mesh canvas ────────────────────────────────────────
  function initMesh() {
    var canvas = document.querySelector('canvas[data-mesh]');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var blobs = [
      { c: '#74C69D', r: 0.55, x: 0.20, y: 0.28, dx: 0.00007, dy: 0.00009, p: 0.0 },
      { c: '#2D6A4F', r: 0.50, x: 0.82, y: 0.20, dx: -0.00009, dy: 0.00006, p: 1.7 },
      { c: '#1B9C82', r: 0.50, x: 0.66, y: 0.82, dx: 0.00006, dy: -0.00008, p: 3.1 },
      { c: '#D9B26A', r: 0.30, x: 0.34, y: 0.74, dx: -0.00005, dy: -0.00006, p: 4.6 }
    ];
    function hexA(hex, a) {
      var n = parseInt(hex.slice(1), 16);
      return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + a + ')';
    }
    function resize() {
      var w = canvas.clientWidth, h = canvas.clientHeight;
      canvas.width = Math.max(1, w * dpr); canvas.height = Math.max(1, h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function draw(t) {
      var w = canvas.clientWidth, h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';
      blobs.forEach(function (b) {
        var ox = reduce ? 0 : Math.sin(t * b.dx + b.p) * 0.12;
        var oy = reduce ? 0 : Math.cos(t * b.dy + b.p) * 0.12;
        var cx = (b.x + ox) * w, cy = (b.y + oy) * h, rad = b.r * Math.max(w, h);
        var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad);
        g.addColorStop(0, hexA(b.c, 0.50));
        g.addColorStop(1, hexA(b.c, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.fill();
      });
      ctx.globalCompositeOperation = 'source-over';
    }
    resize();
    window.addEventListener('resize', resize);
    if (reduce) { draw(0); return; }
    var raf;
    function frame(ts) { draw(ts); raf = requestAnimationFrame(frame); }
    raf = requestAnimationFrame(frame);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) cancelAnimationFrame(raf);
      else raf = requestAnimationFrame(frame);
    });
  }

  // ── Tabs ─────────────────────────────────────────────────────────────────
  function initTabs() {
    document.querySelectorAll('[data-tabs]').forEach(function (root) {
      var btns = root.querySelectorAll('[data-tab]');
      var panels = root.querySelectorAll('[data-panel]');
      function activate(name) {
        btns.forEach(function (b) { b.classList.toggle('is-active', b.getAttribute('data-tab') === name); });
        panels.forEach(function (p) { p.classList.toggle('is-active', p.getAttribute('data-panel') === name); });
      }
      btns.forEach(function (b) {
        b.addEventListener('click', function () { activate(b.getAttribute('data-tab')); });
      });
      if (btns[0]) activate(btns[0].getAttribute('data-tab'));
    });
  }

  // ── Copy-to-clipboard buttons ────────────────────────────────────────────
  function initCopy() {
    document.querySelectorAll('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var text = btn.getAttribute('data-copy');
        function done() {
          if (!btn.getAttribute('data-label')) btn.setAttribute('data-label', btn.textContent);
          btn.classList.add('is-copied');
          btn.textContent = 'Copied';
          setTimeout(function () {
            btn.textContent = btn.getAttribute('data-label');
            btn.classList.remove('is-copied');
          }, 1600);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, done);
        } else { done(); }
      });
    });
  }

  // ── Carousel ─────────────────────────────────────────────────────────────
  function initCarousel() {
    document.querySelectorAll('[data-carousel]').forEach(function (root) {
      var track = root.querySelector('[data-carousel-track]');
      if (!track) return;
      var slides = Array.prototype.slice.call(track.children);
      if (slides.length < 2) return;
      var i = 0, timer = null;
      var dotsWrap = root.querySelector('[data-carousel-dots]');
      var dots = [];
      if (dotsWrap) {
        slides.forEach(function (_, idx) {
          var d = document.createElement('button');
          d.className = 'carousel-dot';
          d.type = 'button';
          d.setAttribute('aria-label', 'Go to slide ' + (idx + 1));
          d.addEventListener('click', function () { go(idx); restart(); });
          dotsWrap.appendChild(d); dots.push(d);
        });
      }
      function go(n) {
        i = (n + slides.length) % slides.length;
        track.style.transform = 'translateX(' + (-i * 100) + '%)';
        dots.forEach(function (d, idx) { d.classList.toggle('is-active', idx === i); });
      }
      function next() { go(i + 1); }
      function restart() { if (timer) clearInterval(timer); if (!reduce) timer = setInterval(next, 5200); }
      go(0); restart();
      root.addEventListener('mouseenter', function () { if (timer) clearInterval(timer); });
      root.addEventListener('mouseleave', restart);
    });
  }

  // ── Mobile nav toggle ────────────────────────────────────────────────────
  function initNav() {
    var toggle = document.querySelector('[data-nav-toggle]');
    var menu = document.querySelector('[data-nav-menu]');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { document.body.classList.remove('nav-open'); });
    });
  }

  // ── Sticky-nav shadow on scroll ──────────────────────────────────────────
  function initStickyNav() {
    var nav = document.querySelector('.site-nav');
    if (!nav) return;
    function onScroll() { nav.classList.toggle('is-scrolled', window.scrollY > 8); }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ── Animated product tour ───────────────────────────────────────────────
  function initTour() {
    var root = document.querySelector('[data-tour]');
    if (!root) return;
    var stages = root.querySelectorAll('.tour-stage');
    var dots = root.querySelectorAll('[data-go]');
    if (!stages.length) return;
    var i = 0, timer = null, chatTimers = [];
    function clearChat() { chatTimers.forEach(clearTimeout); chatTimers = []; }
    function playChat(stage) {
      var chat = stage.querySelector('.tour-chat');
      if (!chat) return;
      var bubbles = chat.querySelectorAll('.tour-bubble');
      if (reduce) {
        bubbles.forEach(function (b) { b.classList.remove('hide'); b.classList.add('show'); });
        return;
      }
      bubbles.forEach(function (b) { b.classList.add('hide'); b.classList.remove('show'); });
      chat.scrollTop = 0;
      var t = 300;
      bubbles.forEach(function (b) {
        chatTimers.push(setTimeout(function () {
          if (!stage.classList.contains('is-active')) return;
          b.classList.remove('hide');
          void b.offsetWidth;
          b.classList.add('show');
          chat.scrollTop = chat.scrollHeight;
        }, t));
        t += 1200;
      });
    }
    function show(n) {
      i = (n + stages.length) % stages.length;
      clearChat();
      stages.forEach(function (s, idx) { s.classList.toggle('is-active', idx === i); });
      dots.forEach(function (d, idx) { d.classList.toggle('is-active', idx === i); });
      playChat(stages[i]);
    }
    function stop() { if (timer) { clearTimeout(timer); timer = null; } }
    function schedule() {
      stop();
      if (reduce) return;
      var dur = parseInt(stages[i].getAttribute('data-dur'), 10) || 4500;
      timer = setTimeout(function () { show(i + 1); schedule(); }, dur);
    }
    dots.forEach(function (d) {
      d.addEventListener('click', function () { show(parseInt(d.getAttribute('data-go'), 10)); schedule(); });
    });
    show(0);
    if ('IntersectionObserver' in window && !reduce) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { if (!timer) { show(i); schedule(); } }
          else { stop(); clearChat(); }
        });
      }, { threshold: 0.3 });
      io.observe(root);
    } else { schedule(); }
  }

  ready(function () {
    initReveal();
    initCountUp();
    initCursorGlow();
    initParallax();
    initMesh();
    initTabs();
    initCopy();
    initCarousel();
    initNav();
    initStickyNav();
    initTour();
  });
})();
