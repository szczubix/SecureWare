/**
 * Minimalny edytor WYSIWYG oparty o contenteditable - bez zewnetrznych
 * zaleznosci (dziala offline, bez CDN). Synchronizuje tresc HTML do ukrytego
 * pola textarea, ktore jest faktycznie wysylane wraz z formularzem.
 */
(function () {
    var COMMANDS = [
        { cmd: 'bold', label: 'B', title: 'Pogrubienie' },
        { cmd: 'italic', label: 'I', title: 'Kursywa' },
        { cmd: 'underline', label: 'U', title: 'Podkreslenie' },
        { cmd: 'formatBlock:H2', label: 'H2', title: 'Naglowek H2' },
        { cmd: 'formatBlock:H3', label: 'H3', title: 'Naglowek H3' },
        { cmd: 'formatBlock:P', label: 'P', title: 'Akapit' },
        { cmd: 'insertUnorderedList', label: '• Lista', title: 'Lista punktowana' },
        { cmd: 'insertOrderedList', label: '1. Lista', title: 'Lista numerowana' },
        { cmd: 'createLink', label: 'Link', title: 'Wstaw link' },
        { cmd: 'removeFormat', label: 'Wyczysc', title: 'Wyczysc formatowanie' },
    ];

    function initEditor(textareaId) {
        var textarea = document.getElementById(textareaId);
        if (!textarea) return;

        textarea.style.display = 'none';

        var wrap = document.createElement('div');

        var toolbar = document.createElement('div');
        toolbar.className = 'editor-toolbar';

        var body = document.createElement('div');
        body.className = 'editor-body';
        body.contentEditable = 'true';
        body.innerHTML = textarea.value || '<p></p>';

        COMMANDS.forEach(function (item) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'button button--ghost button--small';
            btn.style.marginRight = '4px';
            btn.textContent = item.label;
            btn.title = item.title;
            btn.addEventListener('click', function () {
                body.focus();
                if (item.cmd === 'createLink') {
                    var url = window.prompt('Adres URL:', 'https://');
                    if (url) document.execCommand('createLink', false, url);
                } else if (item.cmd.indexOf('formatBlock:') === 0) {
                    document.execCommand('formatBlock', false, item.cmd.split(':')[1]);
                } else {
                    document.execCommand(item.cmd, false, null);
                }
                sync();
            });
            toolbar.appendChild(btn);
        });

        function sync() {
            textarea.value = body.innerHTML;
        }

        body.addEventListener('input', sync);
        body.addEventListener('blur', sync);

        wrap.appendChild(toolbar);
        wrap.appendChild(body);
        textarea.parentNode.insertBefore(wrap, textarea);

        var form = textarea.closest('form');
        if (form) {
            form.addEventListener('submit', sync);
        }
    }

    window.SecureWareEditor = { init: initEditor };
})();
