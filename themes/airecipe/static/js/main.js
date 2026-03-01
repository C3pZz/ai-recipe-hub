/* ============================================================
   AI Recipe Hub - Main JavaScript
   ============================================================ */

(function() {
  'use strict';

  // --- Mobile Navigation ---
  const hamburger = document.querySelector('.hamburger');
  const siteNav = document.querySelector('.site-nav');

  if (hamburger && siteNav) {
    hamburger.addEventListener('click', function() {
      siteNav.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', siteNav.classList.contains('open'));
    });

    // Close on outside click
    document.addEventListener('click', function(e) {
      if (!hamburger.contains(e.target) && !siteNav.contains(e.target)) {
        siteNav.classList.remove('open');
      }
    });
  }

  // --- Search Overlay ---
  const searchToggle = document.querySelector('.search-toggle');
  const searchOverlay = document.querySelector('.search-overlay');
  const searchClose = document.querySelector('.search-close');
  const searchInput = document.getElementById('search-input');

  if (searchToggle && searchOverlay) {
    searchToggle.addEventListener('click', function() {
      searchOverlay.classList.add('active');
      if (searchInput) setTimeout(() => searchInput.focus(), 100);
    });
  }

  if (searchClose && searchOverlay) {
    searchClose.addEventListener('click', function() {
      searchOverlay.classList.remove('active');
    });
  }

  if (searchOverlay) {
    searchOverlay.addEventListener('click', function(e) {
      if (e.target === searchOverlay) {
        searchOverlay.classList.remove('active');
      }
    });
  }

  // Keyboard shortcut: Ctrl+K / Cmd+K
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      if (searchOverlay) {
        searchOverlay.classList.toggle('active');
        if (searchOverlay.classList.contains('active') && searchInput) {
          setTimeout(() => searchInput.focus(), 100);
        }
      }
    }
    if (e.key === 'Escape' && searchOverlay) {
      searchOverlay.classList.remove('active');
    }
  });

  // --- Copy Button for Prompt Boxes ---
  document.querySelectorAll('.copy-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const content = btn.closest('.prompt-box').querySelector('.prompt-box-content');
      if (content) {
        navigator.clipboard.writeText(content.textContent.trim()).then(function() {
          const orig = btn.textContent;
          btn.textContent = 'コピー完了!';
          btn.style.color = '#10b981';
          setTimeout(function() {
            btn.textContent = orig;
            btn.style.color = '';
          }, 2000);
        }).catch(function() {
          // Fallback
          const ta = document.createElement('textarea');
          ta.value = content.textContent.trim();
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          btn.textContent = 'コピー完了!';
          setTimeout(function() { btn.textContent = 'コピー'; }, 2000);
        });
      }
    });
  });

  // --- Active Navigation Link ---
  const currentPath = window.location.pathname;
  document.querySelectorAll('.site-nav a').forEach(function(link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // --- Smooth Scroll for TOC ---
  document.querySelectorAll('.toc-list a').forEach(function(link) {
    link.addEventListener('click', function(e) {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          const offset = 80;
          const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
          window.scrollTo({ top: top, behavior: 'smooth' });
        }
      }
    });
  });

  // --- TOC Active State on Scroll ---
  const tocLinks = document.querySelectorAll('.toc-list a');
  if (tocLinks.length > 0) {
    const headings = Array.from(document.querySelectorAll('.article-content h2, .article-content h3'));

    function updateTocActive() {
      const scrollY = window.pageYOffset + 100;
      let activeId = '';

      headings.forEach(function(h) {
        if (h.offsetTop <= scrollY) {
          activeId = '#' + h.id;
        }
      });

      tocLinks.forEach(function(link) {
        link.classList.toggle('active', link.getAttribute('href') === activeId);
      });
    }

    window.addEventListener('scroll', updateTocActive, { passive: true });
    updateTocActive();
  }

  // --- Affiliate Link Tracking ---
  document.querySelectorAll('.affiliate-btn, [data-affiliate]').forEach(function(link) {
    link.addEventListener('click', function() {
      const tool = link.dataset.tool || 'unknown';
      const position = link.dataset.position || 'unknown';
      // Google Analytics event (if available)
      if (typeof gtag !== 'undefined') {
        gtag('event', 'affiliate_click', {
          'event_category': 'monetization',
          'event_label': tool,
          'value': 1,
          'custom_position': position
        });
      }
    });
  });

  // --- Newsletter Form ---
  const ctaForm = document.querySelector('.cta-form');
  if (ctaForm) {
    ctaForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const emailInput = ctaForm.querySelector('.cta-input');
      if (emailInput && emailInput.value) {
        // Placeholder: integrate with Beehiiv/Mailchimp API
        const btn = ctaForm.querySelector('.btn-primary');
        if (btn) {
          btn.textContent = '登録完了!';
          btn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
          emailInput.value = '';
        }
      }
    });
  }

  // --- Lazy Loading Images ---
  if ('IntersectionObserver' in window) {
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });
    lazyImages.forEach(function(img) { imageObserver.observe(img); });
  }

  // --- Animate on Scroll ---
  if ('IntersectionObserver' in window) {
    const animateEls = document.querySelectorAll('.article-card, .featured-article');
    const animateObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in-up');
          animateObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    animateEls.forEach(function(el) { animateObserver.observe(el); });
  }

  // --- Reading Progress Bar ---
  const article = document.querySelector('.article-content');
  if (article) {
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: linear-gradient(90deg, #6366f1, #06b6d4);
      z-index: 9999;
      transition: width 0.1s ease;
      width: 0%;
    `;
    document.body.appendChild(progressBar);

    window.addEventListener('scroll', function() {
      const articleTop = article.offsetTop;
      const articleHeight = article.offsetHeight;
      const windowHeight = window.innerHeight;
      const scrollY = window.pageYOffset;

      const progress = Math.min(
        Math.max((scrollY - articleTop + windowHeight * 0.5) / articleHeight * 100, 0),
        100
      );
      progressBar.style.width = progress + '%';
    }, { passive: true });
  }

})();
