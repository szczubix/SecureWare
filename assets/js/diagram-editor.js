/**
 * Kreator diagramow przeplywu - canvas z przeciaganymi wezlami i
 * laczeniem ich strzalkami. Stan trzymany w pamieci (state.nodes/edges),
 * przy zapisie serializowany do ukrytych pol formularza (nodes_json/
 * edges_json). Bez zewnetrznych zaleznosci.
 */
(function () {
    var canvasEl = document.getElementById('diagram-canvas');
    if (!canvasEl) return;

    var nodesLayer = document.getElementById('diagram-nodes');
    var edgesLayer = document.getElementById('diagram-edges');
    var inspector  = document.getElementById('diagram-inspector');
    var edgesList  = document.getElementById('diagram-edges-list');
    var hint       = document.querySelector('[data-hint]');
    var widthInput  = document.getElementById('canvas_width');
    var heightInput = document.getElementById('canvas_height');

    var ICONS = JSON.parse(document.getElementById('diagram-icon-library').textContent || '{}');
    var initial = JSON.parse(document.getElementById('diagram-initial-state').textContent || '{"nodes":[],"edges":[]}');

    var state = { nodes: initial.nodes || [], edges: initial.edges || [] };
    var selectedId = null;
    var connectMode = false;
    var connectFrom = null;

    function uid() {
        return 'n' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    }

    function byId(id) {
        for (var i = 0; i < state.nodes.length; i++) {
            if (state.nodes[i].id === id) return state.nodes[i];
        }
        return null;
    }

    function resizeCanvas() {
        var w = parseInt(widthInput.value, 10) || 480;
        var h = parseInt(heightInput.value, 10) || 380;
        canvasEl.style.width = w + 'px';
        canvasEl.style.height = h + 'px';
        edgesLayer.setAttribute('width', w);
        edgesLayer.setAttribute('height', h);
        edgesLayer.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    }
    widthInput.addEventListener('input', resizeCanvas);
    heightInput.addEventListener('input', resizeCanvas);

    function edgePathD(from, to) {
        var x1 = from.x + from.w / 2, y1 = from.y + from.h;
        var x2 = to.x + to.w / 2, y2 = to.y;
        if (Math.abs(x1 - x2) < 0.5) {
            return 'M' + x1 + ',' + y1 + ' L' + x2 + ',' + y2;
        }
        var mid = (y1 + y2) / 2;
        return 'M' + x1 + ',' + y1 + ' C' + x1 + ',' + mid + ' ' + x2 + ',' + mid + ' ' + x2 + ',' + y2;
    }

    function redrawEdges() {
        edgesLayer.innerHTML = '';
        state.edges.forEach(function (edge, i) {
            var from = byId(edge.from), to = byId(edge.to);
            if (!from || !to) return;
            var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', edgePathD(from, to));
            path.setAttribute('class', 'diagram-editor__edge-path');
            edgesLayer.appendChild(path);
        });
    }

    function renderNodes() {
        nodesLayer.innerHTML = '';
        state.nodes.forEach(function (node) {
            var el = document.createElement('div');
            el.dataset.id = node.id;
            el.className = 'diagram-editor__node' + (node.style === 'primary' ? ' is-primary' : '') + (node.id === selectedId ? ' is-selected' : '') + (node.id === connectFrom ? ' is-connect-from' : '');
            el.style.left = node.x + 'px';
            el.style.top = node.y + 'px';
            el.style.width = node.w + 'px';
            el.style.height = node.h + 'px';

            var iconHtml = node.icon && ICONS[node.icon] ? '<span class="diagram-editor__node-icon">' + ICONS[node.icon] + '</span>' : '';
            el.innerHTML = iconHtml +
                '<span class="diagram-editor__node-text">' +
                    '<strong>' + escapeHtml(node.title || '') + '</strong>' +
                    (node.subtitle ? '<small>' + escapeHtml(node.subtitle) + '</small>' : '') +
                '</span>' +
                (node.verified ? '<span class="diagram-editor__node-verified">✓</span>' : '');

            el.addEventListener('pointerdown', function (e) { onNodePointerDown(e, node, el); });
            nodesLayer.appendChild(el);
        });
    }

    function escapeHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function onNodePointerDown(e, node, el) {
        if (connectMode) {
            e.preventDefault();
            handleConnectClick(node.id);
            return;
        }
        selectNode(node.id);

        e.preventDefault();
        var startX = e.clientX, startY = e.clientY;
        var origX = node.x, origY = node.y;
        var maxW = parseInt(widthInput.value, 10) || 480;
        var maxH = parseInt(heightInput.value, 10) || 380;
        var moved = false;

        function onMove(ev) {
            moved = true;
            var dx = ev.clientX - startX, dy = ev.clientY - startY;
            node.x = Math.max(0, Math.min(maxW - node.w, Math.round(origX + dx)));
            node.y = Math.max(0, Math.min(maxH - node.h, Math.round(origY + dy)));
            el.style.left = node.x + 'px';
            el.style.top = node.y + 'px';
            redrawEdges();
        }
        function onUp() {
            document.removeEventListener('pointermove', onMove);
            document.removeEventListener('pointerup', onUp);
            if (moved) renderInspector();
        }
        document.addEventListener('pointermove', onMove);
        document.addEventListener('pointerup', onUp);
    }

    function handleConnectClick(nodeId) {
        if (!connectFrom) {
            connectFrom = nodeId;
            hint.textContent = 'Kliknij węzeł docelowy (albo ten sam, by anulować).';
            renderNodes();
            return;
        }
        if (connectFrom !== nodeId) {
            var exists = state.edges.some(function (e) { return e.from === connectFrom && e.to === nodeId; });
            if (!exists) {
                state.edges.push({ from: connectFrom, to: nodeId });
            }
        }
        connectFrom = null;
        hint.textContent = 'Kliknij węzeł początkowy nowego połączenia (lub "Zakończ łączenie").';
        renderNodes();
        redrawEdges();
        renderEdgesList();
    }

    function selectNode(id) {
        selectedId = id;
        // Tylko przelaczenie klasy na istniejacych elementach (bez pelnego
        // renderNodes()) - to jest wywolywane tez z poczatku przeciagania
        // (onNodePointerDown), gdzie przebudowa DOM zniszczylaby wezel,
        // ktory jest wlasnie chwytany do przeciagniecia.
        Array.prototype.forEach.call(nodesLayer.children, function (el) {
            el.classList.toggle('is-selected', el.dataset.id === id);
        });
        renderInspector();
    }

    function renderInspector() {
        var node = byId(selectedId);
        if (!node) {
            inspector.innerHTML = '<p class="diagram-editor__empty">Kliknij węzeł, aby go edytować.</p>';
            return;
        }

        var iconOptions = Object.keys(ICONS).map(function (name) {
            return '<option value="' + name + '"' + (name === node.icon ? ' selected' : '') + '>' + name + '</option>';
        }).join('');

        inspector.innerHTML =
            '<div class="field"><label>Tytuł</label><input type="text" data-f="title" value="' + escapeAttr(node.title || '') + '"></div>' +
            '<div class="field"><label>Podtytuł</label><input type="text" data-f="subtitle" value="' + escapeAttr(node.subtitle || '') + '"></div>' +
            '<div class="field"><label>Ikona</label><select data-f="icon"><option value="">— brak —</option>' + iconOptions + '</select></div>' +
            '<div class="form-row">' +
                '<div class="field"><label>Szerokość</label><input type="number" data-f="w" value="' + node.w + '" min="60"></div>' +
                '<div class="field"><label>Wysokość</label><input type="number" data-f="h" value="' + node.h + '" min="30"></div>' +
            '</div>' +
            '<div class="field"><label><input type="checkbox" data-f="style" ' + (node.style === 'primary' ? 'checked' : '') + '> Wyróżniony (kolor akcentu)</label></div>' +
            '<div class="field"><label><input type="checkbox" data-f="verified" ' + (node.verified ? 'checked' : '') + '> Odznaka "zweryfikowano"</label></div>' +
            '<button type="button" class="button button--ghost button--small" data-delete-node style="color:#d92d20;">Usuń węzeł</button>';

        inspector.querySelector('[data-f="title"]').addEventListener('input', function (e) { node.title = e.target.value; renderNodes(); });
        inspector.querySelector('[data-f="subtitle"]').addEventListener('input', function (e) { node.subtitle = e.target.value; renderNodes(); });
        inspector.querySelector('[data-f="icon"]').addEventListener('change', function (e) { node.icon = e.target.value; renderNodes(); });
        inspector.querySelector('[data-f="w"]').addEventListener('input', function (e) { node.w = Math.max(60, parseInt(e.target.value, 10) || 60); renderNodes(); redrawEdges(); });
        inspector.querySelector('[data-f="h"]').addEventListener('input', function (e) { node.h = Math.max(30, parseInt(e.target.value, 10) || 30); renderNodes(); redrawEdges(); });
        inspector.querySelector('[data-f="style"]').addEventListener('change', function (e) { node.style = e.target.checked ? 'primary' : 'default'; renderNodes(); });
        inspector.querySelector('[data-f="verified"]').addEventListener('change', function (e) { node.verified = e.target.checked; renderNodes(); });
        inspector.querySelector('[data-delete-node]').addEventListener('click', function () {
            state.nodes = state.nodes.filter(function (n) { return n.id !== node.id; });
            state.edges = state.edges.filter(function (e) { return e.from !== node.id && e.to !== node.id; });
            selectedId = null;
            renderNodes();
            redrawEdges();
            renderInspector();
            renderEdgesList();
        });
    }

    function escapeAttr(s) {
        return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function renderEdgesList() {
        if (!state.edges.length) {
            edgesList.innerHTML = '<p class="diagram-editor__empty">Brak połączeń.</p>';
            return;
        }
        edgesList.innerHTML = '<strong>Połączenia:</strong>' + state.edges.map(function (edge, i) {
            var from = byId(edge.from), to = byId(edge.to);
            var label = (from ? (from.title || from.id) : '?') + ' → ' + (to ? (to.title || to.id) : '?');
            return '<div class="row"><span>' + escapeHtml(label) + '</span><button type="button" class="button button--ghost button--small" data-remove-edge="' + i + '">Usuń</button></div>';
        }).join('');
        edgesList.querySelectorAll('[data-remove-edge]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.edges.splice(parseInt(btn.getAttribute('data-remove-edge'), 10), 1);
                redrawEdges();
                renderEdgesList();
            });
        });
    }

    document.querySelector('[data-add-node]').addEventListener('click', function () {
        var n = state.nodes.length;
        state.nodes.push({
            id: uid(), x: 20 + (n % 3) * 30, y: 20 + (n % 4) * 60, w: 160, h: 56,
            icon: 'shield', title: 'Nowy węzeł', subtitle: '', style: 'default', verified: false,
        });
        renderNodes();
        redrawEdges();
    });

    var connectBtn = document.querySelector('[data-connect-mode]');
    connectBtn.addEventListener('click', function () {
        connectMode = !connectMode;
        connectFrom = null;
        connectBtn.textContent = connectMode ? 'Zakończ łączenie' : 'Połącz węzły';
        connectBtn.classList.toggle('is-active', connectMode);
        hint.textContent = connectMode ? 'Kliknij węzeł początkowy.' : 'Przeciągnij węzły, by je ustawić.';
        renderNodes();
    });

    document.getElementById('diagram-form').addEventListener('submit', function () {
        document.getElementById('nodes_json').value = JSON.stringify(state.nodes);
        document.getElementById('edges_json').value = JSON.stringify(state.edges);
    });

    resizeCanvas();
    renderNodes();
    redrawEdges();
    renderInspector();
    renderEdgesList();
})();
