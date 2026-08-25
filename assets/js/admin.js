/**
 * Obsluga powtarzalnych wierszy pol niestandardowych (custom fields) w
 * formularzach podstron i uslug.
 */
(function () {
    function initRepeatable(containerId) {
        var container = document.getElementById(containerId);
        if (!container) return;

        container.addEventListener('click', function (e) {
            if (e.target.matches('[data-remove-row]')) {
                e.preventDefault();
                e.target.closest('.row').remove();
            }
        });

        var addBtn = document.querySelector('[data-add-row="' + containerId + '"]');
        if (addBtn) {
            addBtn.addEventListener('click', function (e) {
                e.preventDefault();
                var row = document.createElement('div');
                row.className = 'row';
                row.innerHTML = '<input type="text" name="meta_key[]" placeholder="Nazwa pola">' +
                    '<input type="text" name="meta_value[]" placeholder="Wartosc">' +
                    '<button type="button" class="button button--ghost button--small" data-remove-row>Usun</button>';
                container.appendChild(row);
            });
        }
    }

    window.SecureWareAdmin = { initRepeatable: initRepeatable };
})();
