// HEATlab site behavior: click-to-load video, photo album, publication theme filter.
// Everything works without JavaScript too (the video and photos just open as links/thumbnails).

document.addEventListener('DOMContentLoaded', () => {
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
    const pubs = [...document.querySelectorAll('.pub')];
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
    chips.forEach(c => c.addEventListener('click', () => filter(c.dataset.theme)));
    document.querySelectorAll('.theme-papers').forEach(b => b.addEventListener('click', () => {
        filter(b.dataset.theme);
        document.getElementById('publications').scrollIntoView();
    }));
    // Links from project lists to a specific paper: clear the filter so the paper is visible.
    document.querySelectorAll('.project-papers a').forEach(a => a.addEventListener('click', () => filter('')));
    filter('');
});
