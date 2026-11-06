// Accessible keyboard behavior shared by the existing Alpine modal layouts.
document.addEventListener('alpine:initialized', () => {
    let open = null, previousFocus = null;
    const visible = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    const controls = el => [...el.querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]')]
        .filter(node => !node.disabled && visible(node));
    const names = { 'ri-close-line': '닫기', 'ri-delete-bin-line': '삭제', 'ri-edit-line': '수정',
        'ri-arrow-left-s-line': '이전', 'ri-arrow-right-s-line': '다음', 'ri-menu-line': '메뉴 열기',
        'ri-add-line': '추가', 'ri-subtract-line': '축소', 'ri-zoom-in-line': '확대',
        'ri-zoom-out-line': '축소', 'ri-refresh-line': '새로고침', 'ri-message-3-line': '문자 보내기' };
    function update() {
        document.querySelectorAll('button').forEach(button => {
            if (button.textContent.trim() || button.hasAttribute('aria-label')) return;
            const icon = button.querySelector('i');
            const name = button.title || (icon && Object.keys(names).find(key => icon.classList.contains(key)));
            if (name) button.setAttribute('aria-label', names[name] || name);
        });
        const modals = [...document.querySelectorAll('[x-show].fixed.inset-0')].filter(el => visible(el) && el.querySelector('button,input,select,textarea,a'));
        const next = modals.sort((a, b) => (parseInt(getComputedStyle(a).zIndex) || 0) - (parseInt(getComputedStyle(b).zIndex) || 0)).at(-1);
        if (next === open) return;
        if (open && previousFocus?.isConnected && visible(previousFocus)) previousFocus.focus();
        open = next || null;
        if (open) {
            previousFocus = document.activeElement;
            open.setAttribute('role', 'dialog');
            open.setAttribute('aria-modal', 'true');
            const heading = open.querySelector('h2,h3,h4');
            if (heading) {
                heading.id ||= 'dialog-title-' + Math.random().toString(36).slice(2);
                open.setAttribute('aria-labelledby', heading.id);
            } else open.setAttribute('aria-label', '대화상자');
            open.tabIndex = -1;
            (controls(open)[0] || open).focus();
        }
    }
    new MutationObserver(update).observe(document.body, {subtree:true,childList:true,attributes:true,attributeFilter:['style','class']});
    document.addEventListener('keydown', event => {
        if (!open) return;
        if (event.key === 'Escape') {
            const expression = open.getAttribute('x-show');
            if (/^[\w$.]+$/.test(expression)) {
                Alpine.evaluate(open, expression + ' = false');
                event.preventDefault();
            }
        }
        if (event.key === 'Tab') {
            const nodes = controls(open), first = nodes[0], last = nodes.at(-1);
            if (!first) {event.preventDefault();open.focus();}
            else if (event.shiftKey && (document.activeElement === first || !open.contains(document.activeElement))) {event.preventDefault();last.focus();}
            else if (!event.shiftKey && (document.activeElement === last || !open.contains(document.activeElement))) {event.preventDefault();first.focus();}
        }
    });
    update();
});
