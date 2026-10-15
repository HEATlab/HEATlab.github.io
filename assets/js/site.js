// HEATlab site behavior: click-to-load video, photo lightbox, publication theme filter.
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

    // Lightbox for the photo gallery.
    const box = document.querySelector('.lightbox');
    if (box && box.showModal) {
        const img = box.querySelector('img');
        document.querySelectorAll('.gallery-item').forEach(a => {
            a.addEventListener('click', ev => {
                ev.preventDefault();
                img.src = a.href;
                img.alt = a.querySelector('img').alt;
                box.showModal();
            });
        });
        box.addEventListener('click', ev => { if (ev.target !== img) box.close(); });
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
