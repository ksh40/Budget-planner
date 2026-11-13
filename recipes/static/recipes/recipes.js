(function () {
    document.querySelectorAll('.rc-pic').forEach(function (pic) {
        var scroller = pic.querySelector('.rc-scroll');
        var dots = pic.querySelectorAll('.rc-dot');
        var prev = pic.querySelector('.rc-prev');
        var next = pic.querySelector('.rc-next');
        if (!scroller || dots.length < 2) return;

        function current() {
            return Math.round(scroller.scrollLeft / scroller.clientWidth);
        }

        function goTo(n) {
            n = Math.max(0, Math.min(dots.length - 1, n));
            scroller.scrollTo({ left: n * scroller.clientWidth, behavior: 'smooth' });
        }

        function update() {
            var i = current();
            dots.forEach(function (d, n) { d.classList.toggle('on', n === i); });
            if (prev) prev.hidden = i <= 0;
            if (next) next.hidden = i >= dots.length - 1;
        }

        scroller.addEventListener('scroll', update, { passive: true });
        dots.forEach(function (dot, n) {
            dot.addEventListener('click', function () { goTo(n); });
        });
        if (prev) prev.addEventListener('click', function () { goTo(current() - 1); });
        if (next) next.addEventListener('click', function () { goTo(current() + 1); });

        update();
    });
})();