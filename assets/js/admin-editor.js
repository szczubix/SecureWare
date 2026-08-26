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

        var savedRange = null;
        function saveRange() {
            var sel = window.getSelection();
            if (sel && sel.rangeCount && body.contains(sel.anchorNode)) {
                savedRange = sel.getRangeAt(0);
            }
        }
        function restoreRange() {
            body.focus();
            var sel = window.getSelection();
            if (savedRange) {
                sel.removeAllRanges();
                sel.addRange(savedRange);
            }
        }
        body.addEventListener('keyup', saveRange);
        body.addEventListener('mouseup', saveRange);

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

        var imgBtn = document.createElement('button');
        imgBtn.type = 'button';
        imgBtn.className = 'button button--ghost button--small';
        imgBtn.style.marginRight = '4px';
        imgBtn.textContent = 'Obraz';
        imgBtn.title = 'Wstaw obraz z biblioteki mediow lub wgraj nowy';
        imgBtn.addEventListener('click', function () {
            saveRange();
            openMediaPicker(function (media) {
                var alt = window.prompt('Opis obrazu (alt, dla SEO i czytnikow ekranu):', media.filename || '') || '';
                restoreRange();
                var html = '<img src="' + escapeAttr(media.path) + '" alt="' + escapeAttr(alt) + '">';
                document.execCommand('insertHTML', false, html);
                sync();
            });
        });
        toolbar.appendChild(imgBtn);

        var colsBtn = document.createElement('button');
        colsBtn.type = 'button';
        colsBtn.className = 'button button--ghost button--small';
        colsBtn.style.marginRight = '4px';
        colsBtn.textContent = '2 kolumny';
        colsBtn.title = 'Wstaw blok dwoch kolumn tekstu';
        colsBtn.addEventListener('click', function () {
            restoreRange();
            var html = '<div class="content-columns"><div><p>Pierwsza kolumna...</p></div><div><p>Druga kolumna...</p></div></div><p><br></p>';
            document.execCommand('insertHTML', false, html);
            sync();
        });
        toolbar.appendChild(colsBtn);

        var diagBtn = document.createElement('button');
        diagBtn.type = 'button';
        diagBtn.className = 'button button--ghost button--small';
        diagBtn.style.marginRight = '4px';
        diagBtn.textContent = 'Diagram';
        diagBtn.title = 'Wstaw diagram zbudowany w kreatorze';
        diagBtn.addEventListener('click', function () {
            saveRange();
            openDiagramPicker(function (diagram) {
                restoreRange();
                var html = '<div class="sw-diagram-embed" data-diagram="' + escapeAttr(diagram.slug) + '"></div><p><br></p>';
                document.execCommand('insertHTML', false, html);
                sync();
            });
        });
        toolbar.appendChild(diagBtn);

        function escapeAttr(s) {
            return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

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

    var adminBase = (document.querySelector('meta[name="admin-base"]') || {}).content || '';

    function getCsrfToken() {
        // Token jest jeden na sesje (nie per-formularz), wiec dowolne pole
        // _csrf na stronie ma prawidlowa wartosc.
        var field = document.querySelector('[name="_csrf"]');
        return field ? field.value : '';
    }

    function openMediaPicker(onSelect) {
        var overlay = document.createElement('div');
        overlay.className = 'media-picker-overlay';

        var modal = document.createElement('div');
        modal.className = 'media-picker';
        modal.innerHTML =
            '<div class="media-picker__head">' +
                '<strong>Wybierz obraz</strong>' +
                '<button type="button" class="button button--ghost button--small" data-close>Zamknij</button>' +
            '</div>' +
            '<div class="media-picker__upload">' +
                '<input type="file" accept="image/*" data-upload-input>' +
                '<span class="media-picker__status" data-status></span>' +
            '</div>' +
            '<div class="media-picker__grid" data-grid><p style="color:#8a93a3;">Wczytywanie…</p></div>';

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        function close() {
            overlay.remove();
        }
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) close();
        });
        modal.querySelector('[data-close]').addEventListener('click', close);

        function pick(media) {
            close();
            onSelect(media);
        }

        function renderGrid(items) {
            var grid = modal.querySelector('[data-grid]');
            if (!items.length) {
                grid.innerHTML = '<p style="color:#8a93a3;">Brak obrazow w bibliotece - wgraj pierwszy powyzej.</p>';
                return;
            }
            grid.innerHTML = '';
            items.forEach(function (media) {
                var tile = document.createElement('button');
                tile.type = 'button';
                tile.className = 'media-picker__tile';
                tile.title = media.filename;
                tile.innerHTML = '<img src="' + media.path + '" alt="">';
                tile.addEventListener('click', function () { pick(media); });
                grid.appendChild(tile);
            });
        }

        fetch(adminBase + '/media/list.json', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) { renderGrid((data && data.media) || []); })
            .catch(function () {
                modal.querySelector('[data-grid]').innerHTML = '<p style="color:#c0392b;">Nie udalo sie wczytac biblioteki mediow.</p>';
            });

        var fileInput = modal.querySelector('[data-upload-input]');
        var status = modal.querySelector('[data-status]');
        fileInput.addEventListener('change', function () {
            var file = fileInput.files[0];
            if (!file) return;
            status.textContent = 'Wgrywanie…';

            var fd = new FormData();
            fd.append('file', file);
            fd.append('_csrf', getCsrfToken());

            fetch(adminBase + '/media/upload.json', { method: 'POST', body: fd, credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data && data.ok) {
                        status.textContent = '';
                        pick(data.media);
                    } else {
                        status.textContent = (data && data.error) || 'Blad wgrywania.';
                    }
                })
                .catch(function () {
                    status.textContent = 'Blad wgrywania.';
                });
        });
    }

    function openDiagramPicker(onSelect) {
        var overlay = document.createElement('div');
        overlay.className = 'media-picker-overlay';

        var modal = document.createElement('div');
        modal.className = 'media-picker';
        modal.innerHTML =
            '<div class="media-picker__head">' +
                '<strong>Wybierz diagram</strong>' +
                '<button type="button" class="button button--ghost button--small" data-close>Zamknij</button>' +
            '</div>' +
            '<div class="media-picker__grid" data-grid style="grid-template-columns:1fr;"><p style="color:#8a93a3;">Wczytywanie…</p></div>';

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        function close() { overlay.remove(); }
        overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
        modal.querySelector('[data-close]').addEventListener('click', close);

        fetch(adminBase + '/diagrams/list.json', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var items = (data && data.diagrams) || [];
                var grid = modal.querySelector('[data-grid]');
                if (!items.length) {
                    grid.innerHTML = '<p style="color:#8a93a3;">Brak zapisanych diagramow - utworz jeden w Kreatorze diagramow.</p>';
                    return;
                }
                grid.innerHTML = '';
                items.forEach(function (diagram) {
                    var row = document.createElement('button');
                    row.type = 'button';
                    row.className = 'button button--ghost';
                    row.style.cssText = 'width:100%;justify-content:flex-start;margin-bottom:6px;';
                    row.textContent = diagram.name + ' (' + diagram.slug + ')';
                    row.addEventListener('click', function () { close(); onSelect(diagram); });
                    grid.appendChild(row);
                });
            })
            .catch(function () {
                modal.querySelector('[data-grid]').innerHTML = '<p style="color:#c0392b;">Nie udalo sie wczytac listy diagramow.</p>';
            });
    }

    window.SecureWareEditor = { init: initEditor };
})();
