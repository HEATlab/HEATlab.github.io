// HEATlab site behavior: click-to-load video, photo album, publication theme filter.
// Everything works without JavaScript too (the video and photos just open as links/thumbnails).

document.addEventListener('DOMContentLoaded', () => {
    // Header robot: at the top of the page it floats in the hero (above the eyebrow) while the header spells
    // HEATlab with a plain A; scrolling shrinks it up into the A's place. Skipped for reduced motion.
    const bot = document.querySelector('.brand-bot');
    const spot = document.querySelector('.hero-bot');
    if (bot && spot && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.classList.add('bot-fly');
        const letterA = document.querySelector('.brand-a');
        const img = bot.querySelector('img'), source = bot.querySelector('source');
        const still = { img: img.getAttribute('src'), dark: source && source.getAttribute('srcset') };
        const wink = { img: still.img.replace('heatbot.svg', 'heatbot-wink.svg'), dark: still.dark && still.dark.replace('heatbot-dark.svg', 'heatbot-wink-dark.svg') };
        let winking = null;
        const setWink = on => {                       // the animated (winking) robot while it's big; the still one once landed
            if (on === winking) return;
            winking = on;
            const v = on ? wink : still;
            img.src = v.img;
            if (source && v.dark) source.srcset = v.dark;
        };
        let home, start;                              // the robot's place in the logo; its hero spot at scroll 0
        const measure = () => {
            bot.style.transform = 'none';
            home = bot.getBoundingClientRect();
            const r = spot.getBoundingClientRect();
            start = { x: r.left, bottom: r.bottom + window.scrollY, w: r.width };
            place();
        };
        // The robot rides along with the hero (its feet keep their distance above the eyebrow) while it shrinks;
        // it lands in the A's place exactly when it reaches the header.
        const place = () => {
            const homeH = home.height, startH = start.w * homeH / home.width;
            const range = Math.max(80, start.bottom - home.top - homeH);
            const t = Math.min(1, window.scrollY / range);
            const w = start.w + (home.width - start.w) * t, h = w * homeH / home.width;
            const bottom = start.bottom - window.scrollY;    // the spot's bottom, moving with the page
            const y = Math.max(home.top, bottom - h);
            const x = start.x + (home.left - start.x) * t;
            bot.style.transform = t >= 1 ? 'none' : `translate(${x - home.left}px, ${y - home.top}px) scale(${w / home.width})`;
            bot.classList.toggle('floating', t === 0);
            bot.classList.toggle('flying', t < 1);
            setWink(t < 1);
            if (letterA) letterA.style.opacity = String(1 - Math.min(1, Math.max(0, (t - 0.8) / 0.2)));
        };
        measure();
        window.addEventListener('scroll', place, { passive: true });
        window.addEventListener('resize', measure);
        window.addEventListener('load', measure);
    }
    // Video: load YouTube only when clicked, so the page stays light.
    document.querySelectorAll('[data-youtube]').forEach(btn => {
        btn.addEventListener('click', () => {
            const iframe = document.createElement('iframe');
            iframe.src = `https://www.youtube-nocookie.com/embed/${btn.dataset.youtube}?autoplay=1&rel=0`;
            iframe.title = btn.getAttribute('aria-label').replace(/^Play video: /, '');
            iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
            iframe.allowFullscreen = true;
            btn.replaceChildren(iframe);
        }, { once: true });
    });

    // Photo album: click a photo to open it; arrows, arrow keys, or swiping move through the album.
    const box = document.querySelector('.lightbox');
    if (box && box.showModal) {
        const img = box.querySelector('img');
        const caption = box.querySelector('.lightbox-caption');
        const count = box.querySelector('.lightbox-count');
        const items = [...document.querySelectorAll('.gallery-item')];
        let current = 0;
        function show(i) {
            current = (i + items.length) % items.length;
            const a = items[current], alt = a.querySelector('img').alt;
            img.src = a.href;
            img.alt = alt;
            caption.textContent = alt;
            count.textContent = `${current + 1} / ${items.length}`;
            // Preload the neighbors so moving through the album is instant.
            [current - 1, current + 1].forEach(n => { new Image().src = items[(n + items.length) % items.length].href; });
        }
        items.forEach((a, i) => a.addEventListener('click', ev => {
            ev.preventDefault();
            show(i);
            box.showModal();
        }));
        box.querySelector('.lightbox-prev').addEventListener('click', () => show(current - 1));
        box.querySelector('.lightbox-next').addEventListener('click', () => show(current + 1));
        box.querySelector('.lightbox-close').addEventListener('click', () => box.close());
        box.addEventListener('click', ev => { if (ev.target === box || ev.target.classList.contains('lightbox-figure')) box.close(); });
        box.addEventListener('keydown', ev => {
            if (ev.key === 'ArrowLeft') show(current - 1);
            if (ev.key === 'ArrowRight') show(current + 1);
        });
        let startX = null;
        box.addEventListener('touchstart', ev => { startX = ev.touches[0].clientX; }, { passive: true });
        box.addEventListener('touchend', ev => {
            if (startX === null) return;
            const dx = ev.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 40) show(current + (dx < 0 ? 1 : -1));
            startX = null;
        });
    }

    // Publication filter by research theme (from data/themes.json): chips, plus the "See the papers" buttons on each theme card.
    const pubs = [...document.querySelectorAll('#pub-all .pub')];
    const years = [...document.querySelectorAll('.pub-year')];
    const chips = [...document.querySelectorAll('.chip')];
    function filter(theme) {
        pubs.forEach(p => { p.hidden = theme && !p.dataset.themes.split(' ').includes(theme); });
        years.forEach(h => {
            let el = h.nextElementSibling, any = false;
            while (el && !el.classList.contains('pub-year')) { if (!el.hidden) any = true; el = el.nextElementSibling; }
            h.hidden = !any;
        });
        chips.forEach(c => {
            const on = c.dataset.theme === theme;
            c.classList.toggle('active', on);
            c.setAttribute('aria-pressed', on);
        });
    }
    // Selected publications show first; the full list opens on request (without JS both show).
    const all = document.getElementById('pub-all');
    const showAllBtn = document.getElementById('pub-show-all');
    const showAll = () => { if (all) all.hidden = false; if (showAllBtn) showAllBtn.hidden = true; };
    if (all && showAllBtn && document.querySelector('#pub-selected .pub')) {
        all.hidden = true;
        showAllBtn.hidden = false;
        showAllBtn.addEventListener('click', () => { showAll(); all.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    }
    chips.forEach(c => c.addEventListener('click', () => filter(c.dataset.theme)));
    document.querySelectorAll('.theme-papers').forEach(b => b.addEventListener('click', () => {
        showAll();
        filter(b.dataset.theme);
        document.getElementById('publications').scrollIntoView();
    }));
    // Links from project lists to a specific paper: clear the filter so the paper is visible.
    document.querySelectorAll('.project-papers a').forEach(a => a.addEventListener('click', () => { showAll(); filter(''); }));
    filter('');
});

/* ---- Analytics events: which links people click and which sections they reach ----
   Sends GA4 events (names show up under Reports > Engagement > Events without setup):
   pdf_click, email_click, profile_click, doi_click, cite_click, bib_download,
   and view_<section id> the first time a section scrolls into view. */
(function () {
    if (typeof window.gtag !== 'function') return;
    var send = function (name, params) {
        try { window.gtag('event', name, Object.assign({ transport_type: 'beacon' }, params || {})); } catch (e) {}
    };
    var PROFILES = /github\.com|scholar\.google|linkedin\.com|researchgate\.net|orcid\.org|bsky\.app/i;
    document.addEventListener('click', function (e) {
        var el = e.target.closest ? e.target.closest('a, button') : null;
        if (!el) return;
        var href = el.getAttribute('href') || '';
        var label = (el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 100);
        var p = { link_url: href.slice(0, 300), link_text: label };
        if (/\.pdf(\?|#|$)/i.test(href)) send('pdf_click', p);
        else if (/^mailto:/i.test(href)) send('email_click', { link_text: label });
        else if (PROFILES.test(href)) send('profile_click', p);
        else if (/doi\.org\//i.test(href)) send('doi_click', p);
        else if (/\.bib(\?|#|$)/i.test(href)) send('bib_download', p);
        else if (/\bcite\b/i.test(label) || el.hasAttribute('data-cite')) send('cite_click', p);
    }, true);
    if (!('IntersectionObserver' in window)) return;
    var seen = {};
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
            var id = en.target.id;
            if (en.isIntersecting && !seen[id]) {
                seen[id] = true;
                send('view_' + id.replace(/[^a-z0-9_]/gi, '_'));
                io.unobserve(en.target);
            }
        });
    }, { threshold: 0.25 });
    document.querySelectorAll('section[id]').forEach(function (s) { io.observe(s); });
})();
