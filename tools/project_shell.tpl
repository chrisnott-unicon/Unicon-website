<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>@@TITLE@@</title>
    <link rel="icon" href="https://wsrv.nl/?url=raw.githubusercontent.com/chrisnott-unicon/UniconLogo/main/UniconBlk.png&amp;w=64&amp;h=64&amp;fit=contain&amp;output=png">
    <link rel="canonical" href="@@URL@@">
    <meta name="description" content="@@DESC@@">
    <meta property="og:title" content="@@OGTITLE@@">
    <meta property="og:description" content="@@DESC@@">
    <meta property="og:image" content="@@OGIMG@@">
    <meta property="og:url" content="@@URL@@">
    <meta property="og:type" content="website">

    <script async src="https://www.googletagmanager.com/gtag/js?id=G-TWWS9BQM18"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-TWWS9BQM18');
    </script>

    <link rel="preconnect" href="https://cdn.tailwindcss.com">
    <link rel="preconnect" href="https://cdnjs.cloudflare.com" crossorigin>
    <link rel="preconnect" href="https://wsrv.nl">
    <link rel="dns-prefetch" href="https://raw.githubusercontent.com">
    <link rel="dns-prefetch" href="https://www.googletagmanager.com">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { unicon: { black: '#0a0a0a', dark: '#1c1c1c', slate: '#f4f4f5', green: '#475c4d', border: '#e5e7eb' } },
                    fontFamily: { sans: ['"Century Gothic"', 'sans-serif'], mono: ['ui-monospace', 'monospace'] },
                    letterSpacing: { tighter: '-0.04em', tight: '-0.02em', widest: '0.2em' }
                }
            }
        }
    </script>
    <style>
        body { background-color: #ffffff; color: #0a0a0a; -webkit-font-smoothing: antialiased; margin: 0; padding: 0; overflow-x: hidden; }
        .bg-blueprint { background-image: linear-gradient(to right, #f3f4f6 1px, transparent 1px), linear-gradient(to bottom, #f3f4f6 1px, transparent 1px); background-size: 4rem 4rem; }
        .text-outline { color: transparent; -webkit-text-stroke: 1px #0a0a0a; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-up { animation: fadeUp 1s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; }
        .delay-100 { animation-delay: 100ms; }
        .delay-200 { animation-delay: 200ms; }
        .link-underline { position: relative; }
        .link-underline::after { content: ''; position: absolute; width: 0; height: 1px; bottom: -2px; left: 0; background-color: #475c4d; transition: width 0.3s ease; }
        .link-underline:hover::after { width: 100%; }
        
        .whatsapp-fab { position: fixed; bottom: calc(30px + env(safe-area-inset-bottom) + var(--fab-lift, 0px)); right: 30px; background-color: #25D366; color: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 9998; transition: transform 0.3s ease, bottom 0.3s ease; text-decoration: none; }
        .whatsapp-fab:hover { transform: scale(1.1); }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
    @@SCHEMA@@
</head>
<body class="font-sans pt-16 sm:pt-20">

    <a href="https://wa.me/27664834709?text=@@WAMSG@@" target="_blank" rel="noopener noreferrer" class="whatsapp-fab" aria-label="Chat with us on WhatsApp">
        <i class="fa-brands fa-whatsapp"></i>
    </a>

    <!-- NATIVE NAVIGATION BAR -->
    @@NAV@@

    @@BODY@@

    @@FOOTER@@

    <!-- POPIA BANNER -->
    <div id="cookie-banner" class="fixed bottom-0 left-0 w-full bg-[#0a0a0a]/95 backdrop-blur-md border-t border-[#475c4d] z-[9999] transform translate-y-full transition-transform duration-500 flex flex-col sm:flex-row items-center justify-between p-4 sm:px-8 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
        <div class="flex items-start gap-4 mb-4 sm:mb-0">
            <i class="fa-solid fa-cookie-bite text-[#475c4d] text-xl mt-1 hidden sm:block"></i>
            <div>
                <h4 class="text-white text-xs font-bold uppercase tracking-widest mb-1">Data & Privacy Control</h4>
                <p class="text-gray-400 text-[10px] sm:text-xs font-light leading-relaxed max-w-3xl">
                    Unicon Construction utilizes essential cookies and analytics to optimize user experience and track site performance. By proceeding, you consent to our digital privacy framework in accordance with the POPI Act.
                </p>
            </div>
        </div>
        <div class="flex gap-3 w-full sm:w-auto">
            <button id="accept-cookies" class="flex-1 sm:flex-none px-6 py-2.5 bg-[#475c4d] text-white text-[10px] font-bold uppercase tracking-widest hover:bg-white hover:text-black transition-colors whitespace-nowrap rounded-sm">
                Acknowledge & Accept
            </button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const yearElem = document.getElementById('year-footer');
            if (yearElem) yearElem.textContent = new Date().getFullYear();

            const mobileBtn = document.getElementById('mobile-menu-btn');
            const mobileMenu = document.getElementById('mobile-menu');
            const mobileIcon = mobileBtn ? mobileBtn.querySelector('i') : null;
            if (mobileBtn && mobileMenu) {
                const setMenu = (closed) => {
                    mobileMenu.classList.toggle('translate-x-full', closed);
                    mobileBtn.setAttribute('aria-expanded', String(!closed));
                    if (mobileIcon) {
                        mobileIcon.classList.toggle('fa-xmark', !closed);
                        mobileIcon.classList.toggle('fa-bars', closed);
                    }
                };
                mobileBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    setMenu(!mobileMenu.classList.contains('translate-x-full'));
                });
                // Tapping a link or anywhere outside should dismiss the panel;
                // without this the only way out is finding the hamburger again.
                mobileMenu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => setMenu(true)));
                document.addEventListener('click', (e) => {
                    if (!mobileMenu.classList.contains('translate-x-full')
                        && !mobileMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
                        setMenu(true);
                    }
                });
                document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(true); });
            }

            // Keep the WhatsApp button clear of the consent banner, which
            // otherwise sits underneath it and loses part of its Accept button.
            const banner = document.getElementById('cookie-banner');
            const acceptBtn = document.getElementById('accept-cookies');
            const lift = () => {
                document.documentElement.style.setProperty(
                    '--fab-lift', banner && !banner.classList.contains('translate-y-full')
                        ? banner.offsetHeight + 16 + 'px' : '0px');
            };
            if (banner && acceptBtn) {
                if (!localStorage.getItem('unicon_cookie_consent')) {
                    setTimeout(() => { banner.classList.remove('translate-y-full'); lift(); }, 1500);
                }
                acceptBtn.addEventListener('click', () => {
                    localStorage.setItem('unicon_cookie_consent', 'true');
                    banner.classList.add('translate-y-full');
                    lift();
                });
                window.addEventListener('resize', lift);
            }
        });
    </script>
    <script>
    // Phone, WhatsApp and email are the main enquiry routes besides the form;
    // without this none of them are visible in analytics. Runs inline at end of
    // body (DOM already parsed) so the page keeps a single DOMContentLoaded.
    (function () {
        if (typeof gtag !== 'function') return;
        document.querySelectorAll('a[href^="tel:"], a[href^="mailto:"], a[href*="wa.me/"]').forEach(function (a) {
            a.addEventListener('click', function () {
                var h = a.getAttribute('href') || '';
                var m = h.indexOf('tel:') === 0 ? 'phone' : (h.indexOf('mailto:') === 0 ? 'email' : 'whatsapp');
                gtag('event', 'contact_click', { method: m, page_path: location.pathname });
            });
        });
    })();
    </script>
</body>
</html>
