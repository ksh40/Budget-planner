(function () {
    var root = document.getElementById('wn-root');
    if (!root) return;

    var authed = root.dataset.auth === '1';
    var toast = document.getElementById('wn-toast');
    var toastText = toast.querySelector('.wn-toast-text');
    var toastLink = document.getElementById('wn-toast-link');
    var toastTimer;

    function showToast(text, withLink) {
        toastText.textContent = text;
        toastLink.hidden = !withLink;
        if (withLink) {
            toastLink.href = root.dataset.registerUrl + '?next=' +
                encodeURIComponent(location.pathname + location.search);
        }
        toast.hidden = false;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toast.hidden = true; }, 5000);
    }

    var SIGN_UP_TEXT = 'Sign up to save posts. It only takes a username and a password.';

    function post(params) {
        return fetch(root.dataset.toggleUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': root.dataset.csrf,
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams(params)
        }).then(function (r) {
            if (!r.ok) { throw r; }
            return r.json();
        });
    }

    var userBtn = document.getElementById('wn-user');
    var menu = document.getElementById('wn-menu');

    function closeMenu() {
        if (!menu) return;
        menu.hidden = true;
        if (userBtn) {
        userBtn.setAttribute('aria-expanded', 'false');
    }
    }

    if (userBtn && menu) {
        userBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            var opening = menu.hidden;
            menu.hidden = !opening;
            userBtn.setAttribute('aria-expanded', opening ? 'true' : 'false');
        });
        document.addEventListener('click', function (e) {
            if (!menu.contains(e.target)) closeMenu();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeMenu();
        });
    }



    var mobileToggle = document.getElementById('mobile-menu-toggle');
    var mobileMenu = document.getElementById('mobile-menu');

    function closeMobileMenu() {
        if (!mobileToggle || !mobileMenu) return;

        mobileMenu.hidden = true;
        mobileToggle.setAttribute('aria-expanded', 'false');
        mobileToggle.setAttribute('aria-label', 'Open menu');
    }

    if (mobileToggle && mobileMenu) {
        mobileToggle.addEventListener('click', function (e) {
            e.stopPropagation();

            var opening = mobileMenu.hidden;
            mobileMenu.hidden = !opening;

            mobileToggle.setAttribute('aria-expanded', String(opening));
            mobileToggle.setAttribute(
                'aria-label',
                opening ? 'Close menu' : 'Open menu'
            );
        });

        document.addEventListener('click', function (e) {
            if (
                !mobileToggle.contains(e.target) &&
                !mobileMenu.contains(e.target)
            ) {
                closeMobileMenu();
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeMobileMenu();
        });

        mobileMenu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', closeMobileMenu);
        });
    }



    function paint(btn, saved, count) {
        btn.classList.toggle('is-saved', saved);
        btn.setAttribute('aria-pressed', saved ? 'true' : 'false');
        btn.querySelector('.bm-label').textContent = saved ? 'Nimekumark' : 'Hmmmmmm🤔';
        var c = btn.querySelector('.bm-count');
        c.textContent = count;
        c.hidden = !count;
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.bm-btn');
        if (!btn) return;

        if (!authed) {
            showToast(SIGN_UP_TEXT, true);
            return;
        }
        if (btn.dataset.busy) return;

        var wasSaved = btn.classList.contains('is-saved');
        var wasCount = parseInt(btn.querySelector('.bm-count').textContent, 10) || 0;
        paint(btn, !wasSaved, Math.max(0, wasCount + (wasSaved ? -1 : 1)));
        btn.dataset.busy = '1';

        post({ kind: btn.dataset.kind, pk: btn.dataset.pk })
            .then(function (d) { paint(btn, d.saved, d.count); })
            .catch(function (r) {
                paint(btn, wasSaved, wasCount);
                if (r && r.status === 401) {
                    showToast(SIGN_UP_TEXT, true);
                } else {
                    showToast("Couldn't save that. Try again.", false);
                }
            })
            .then(function () { delete btn.dataset.busy; });
    });

    var list = document.getElementById('wn-saved');
    var editBtn = document.getElementById('wn-edit');
    var empty = document.getElementById('wn-empty');

    if (list && editBtn) {
        editBtn.addEventListener('click', function () {
            var on = list.classList.toggle('is-editing');
            editBtn.textContent = on ? 'Done' : 'Edit';
        });

        list.addEventListener('click', function (e) {
            var rm = e.target.closest('.wn-remove');
            if (!rm) return;
            rm.disabled = true;
            post({ kind: rm.dataset.kind, pk: rm.dataset.pk, mode: 'remove' })
                .then(function () {
                    rm.closest('.wn-card').remove();
                    if (!list.children.length) {
                        list.hidden = true;
                        editBtn.hidden = true;
                        if (empty) empty.hidden = false;
                    }
                })
                .catch(function () {
                    rm.disabled = false;
                    showToast("Couldn't remove that. Try again.", false);
                });
        });
    }

    document.querySelectorAll('[data-autosubmit]').forEach(function (input) {
        input.addEventListener('change', function () {
            if (input.files.length) input.form.submit();
        });
    });
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-toggle-pass]');
        if (!btn) return;
        var input = btn.parentElement.querySelector('input');
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.classList.toggle('is-on', show);
        btn.setAttribute('aria-pressed', show ? 'true' : 'false');
        btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
    document.addEventListener('click', function (e) {
        var close = e.target.closest('.message-close');
        if (close) close.closest('.message').remove();
    });
    document.querySelectorAll('.plan-messages .message').forEach(function (m) {
        setTimeout(function () { m.remove(); }, 6000);
    });
    
    
})();
