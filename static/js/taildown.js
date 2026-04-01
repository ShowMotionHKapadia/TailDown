//Displays a toast notification using the Toastify library.
//'type' controls the background color: error/danger = red, warning = yellow, info = blue, default = green.
function showNotification(msg, type) {
    var bgColor = "#00D062"; 
    if (type === "error" || type === "danger") {
        bgColor = "#fd1515e9"; 
    } else if (type === "warning") {
        bgColor = "#f9d338"; 
    } else if (type === "info") {
        bgColor = "#29d0f9"; 
    }

    Toastify({
        text: msg,
        duration: 3000,
        close: true,    
        gravity: "bottom",
        position: "right",
        stopOnFocus: true,
        offset: { x: 20, y: 80 },
        style: {
            background: bgColor,
            width: "auto",
            minWidth: "250px",
            maxWidth: "350px",
            minHeight: "50px",     
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
            fontSize: "15px",
            fontWeight: "500",
            borderRadius: "8px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
        }
    }).showToast();
}

//Get Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(cookie => {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
}

// AJAX DELETE
// Usage: ajaxDelete(url, onSuccess, onError)
// Automatically attaches CSRF token to every request.
function ajaxDelete(url, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'POST',           // POST (not DELETE) — works with Django's @require_POST + CSRF
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),   // CSRF token from cookie
            'X-Requested-With': 'XMLHttpRequest'     // Marks request as AJAX on Django's side
        },
        success: function(response) {
            console.log('=== RAW RESPONSE ===', JSON.stringify(response));
            console.log('=== response.status ===', response.status);
            console.log('=== typeof response ===', typeof response);
        if (response.status === 'success') {
            console.log('=== GOING TO onSuccess ===');
            onSuccess(response);
        } else {
            console.log('=== GOING TO onError ===');
            onError(response);
        }
        },
        error: function(xhr) {
            console.log('=== AJAX ERROR ===', xhr.status, xhr.responseText);
            const msg = xhr.status === 403 ? 'Permission denied.' : xhr.status === 404 ? 'Item not found.' : 'Something went wrong.';
            onError({ message: msg });
        }
    });
}

// AJAX Get
// Usage: ajaxGet(url, onSuccess, onError)
// Automatically attaches CSRF token to every request to get data from the server.
function ajaxGetData(url, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'GET',           
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),   
            'X-Requested-With': 'XMLHttpRequest'    
        },
        success: function(response) {
        if (response.status === 'success') {
            onSuccess(response);
        } else {
            onError(response);
        }
        },
        error: function(xhr) {
        const msg = xhr.status === 403 ? 'Permission denied. You can only delete your own items.' : xhr.status === 404 ? 'Item not found — it may have already been removed.' : 'Something went wrong. Please try again.';
        onError({ message: msg });
        }
    });
}

//Edit User Order Model
function openEditModal(uuid) {
    // Set form action
    $('#editForm').attr('action', `/customer/order/${uuid}/edit/`);

    // Show modal with loading state
    $('#editModal').removeClass('hidden');
    $('body').css('overflow', 'hidden');
    $('#editFormContent').addClass('opacity-50 pointer-events-none');

    // Fetch order data using jQuery AJAX
    $.ajax({
        url: `/customer/order/${uuid}/data/`,
        type: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
            // Populate all fields with live data from DB
            $('#edit_orderName').val(data.orderName);
            $('#edit_deliverBy').val(data.deliverBy);
            $('#edit_quantity').val(data.quantity);
            $('#edit_showName').val(data.showName);
            $('#edit_cableSize').val(data.cableSize);
            $('#edit_cableFinishes').val(data.cableFinishes);
            $('#edit_cableLengthFt').val(data.cableLengthFt);
            $('#edit_cableLengthIn').val(data.cableLengthIn);
            $('#edit_topType').val(data.topType);
            $('#edit_endType').val(data.endType);
            $('#edit_turnbuckle').prop('checked', data.turnbuckle);   //? true : false
            $('#edit_chain').prop('checked', data.chain).trigger('change');               // ? true: false
            $('#edit_tcOrder').val(data.tcOrder|| 'none');
            $('#edit_turnbuckleSize').val(data.turnbuckleSize || '');
            $('#edit_chainLength').val(data.chainLength || '');
            $('#edit_status').val(data.status);

            // Toggle chain length visibility
            if (data.chain) {
                $('#edit_chainLength_group').show();
            } else {
                $('#edit_chainLength_group').hide();
            }

            // Remove loading state
            $('#editFormContent').removeClass('opacity-50 pointer-events-none');
        },
        error: function(xhr) {
            const msg = xhr.status === 403
                ? 'Permission denied. You cannot edit this order.'
                : xhr.status === 404
                ? 'Order not found — it may have already been removed.'
                : 'Something went wrong. Please try again.';

            closeEditModal();
            alert(msg);
        }
    });
}

//Close User Order Model 
function closeEditModal() {
    $('#editModal').addClass('hidden');
    $('body').css('overflow', '');
}

//Reads the current value of a text input by its 'name' attribute.
//Returns a rendered summary row if the field has a value, otherwise returns an empty string.
function getInputText(name, label){
    let $el = $(`input[name="${name}"]`);
    if ($el.val().length > 0) {
        return renderRow(label, $el.val());
    }
    return "";
}

//Reads the selected option's visible text from a <select> by its 'name' attribute.
//Skips placeholder options (empty value) and returns an empty string if nothing is selected.
function getSelectText(name, label) {
    let $el = $(`select[name="${name}"]`);
    let txt = $el.find("option:selected").text();
    let val = $el.val();
    if (val && val !== "" && val !== null) {
        return renderRow(label, txt);
    }
    return "";
}

//Reads whichever radio button in a group is currently checked.
//Capitalizes the first letter of the value for display (e.g. "big" → "Big").
function getRadioText(name, label) {
    let $checked = $(`input[name="${name}"]:checked`);
    if ($checked.length) {
        let val = $checked.val();
        return renderRow(label, val.charAt(0).toUpperCase() + val.slice(1));
    }
    return "";
}

//Checks which hardware checkboxes (turnbuckle / chain) are ticked.
//Joins multiple selections with " & " for display (e.g. "Turnbuckle & Chain").
function getCheckboxStatus() {
    let hardware = [];
    if ($('input[name="turnbuckle"]').is(':checked')) hardware.push("Turnbuckle");
    if ($('input[name="chain"]').is(':checked')) hardware.push("Chain");
    
    if (hardware.length > 0) {
        return renderRow("Hardware", hardware.join(" & "));
    }
    return "";
}

//Builds a single label/value row as an HTML string for the Order Summary panel.
function renderRow(label, value) {
    return `
        <div class="flex justify-between items-start border-b border-slate-200 pb-2">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">${label}</span>
            <span class="text-sm font-bold text-slate-800 text-right ml-4">${value}</span>
        </div>`;
}

// Reads the cable length value and the selected unit radio button.
function getCableLengthText() {
    let ft = $('input[name="cableLengthFt"]').val();
    let inches = $('input[name="cableLengthIn"]').val();
    let parts = [];
    if (ft && parseInt(ft) > 0) parts.push(ft + "'");
    if (inches && parseInt(inches) > 0) parts.push(inches + '"');
    if (parts.length > 0) {
        return renderRow("Cable Length", parts.join(" "));
    }
    return "";
}

//Controls two pieces of conditional UI based on the hardware checkbox state:
//1.Turnbuckle Size selector — shown/enabled only when the turnbuckle is checked.
//2.Order dropdown options — filtered so only valid combinations are visible.
function handleHardwareLogic() {
    const isTB = $('input[name="turnbuckle"]').is(':checked');
    const isChain = $('input[name="chain"]').is(':checked');
    
    const $orderSelect = $('select[name="tcOrder"]');
    const $sizeSelect = $('select[name="turnbuckleSize"]');
    const $sizeContainer = $sizeSelect.closest('.space-y-3');
    const $chainLenght = $('select[name="chainLength"]');
    const $selectChainLength = $chainLenght.closest('.space-y-3');

    //Show the TB size field only when a turnbuckle is part of the order
    if (isTB) {
        $sizeContainer.show(); // Matches requirements: Show TB size
        $sizeSelect.prop('disabled', false);
    } else {
        //Hide and disable so the empty value is not accidentally submitted
        $sizeContainer.hide(); //Matches requirements: Hide TB size
        $sizeSelect.prop('disabled', true).val("");
    }

    if (isChain) {
        $selectChainLength.show();
        $chainLenght.prop('disabled', false);
    }else{
        $selectChainLength.hide(); //Matches requirements: Hide TB size
        $chainLenght.prop('disabled', true).val("");
    }

    //Reset all options to hidden first, then reveal only the valid ones
    $orderSelect.find('option').hide(); 
    $orderSelect.find('option[value=""]').show(); //Placeholder
    // $orderSelect.find('option[value="none"]').show(); //Always show "None" by default

    if (isTB && !isChain) {
        //Only turnbuckle checked — "Only Turnbuckle" is the sole valid order
        $orderSelect.find('option[value="OT"]').show(); //Show Only TB

    } else if (!isTB && isChain) {
        //Only chain checked — "Only Chain" is the sole valid order
        $orderSelect.find('option[value="OC"]').show(); //Show Only Chain

    } else if (isTB && isChain) {
        //Both checked — user chooses which hardware comes first in the assembly
        $orderSelect.find('option[value="TC"]').show(); //Turnbuckle then Chain
        $orderSelect.find('option[value="CT"]').show(); //Chain then Turnbuckle

        //Single-hardware and "None" options are not valid when both are selected
        $orderSelect.find('option[value="OT"], option[value="OC"], option[value="none"]').hide();

    } else {
        //Neither checked — force the order to "None" automatically
        $orderSelect.find('option[value="none"]').show();
        // $orderSelect.val('none');
    }

    updateSummary();
}

//Rebuilds the Order Summary panel in the aside from the current form field values.
//Shows a placeholder message if no fields have been filled in yet.
function updateSummary() {

    //Re-query the summary container each call in case the DOM has been re-rendered
    const $summaryBox = $('aside .slim-scroll'); 
    if ($summaryBox.length === 0) return;

    let summaryHtml = '<div class="w-full space-y-4">';

    //Collect each field's current value; helpers return "" if the field is empty
    summaryHtml += getInputText("orderName", "Order Name");
    summaryHtml += getInputText("deliverBy", "Deliver By");
    summaryHtml += getInputText("quantity", "Quantity");
    summaryHtml += getSelectText("showName", "Show");
    summaryHtml += getSelectText("cableFinishes", "Finish");
    summaryHtml += getSelectText("cableSize", "Cable Size");
    summaryHtml += getCableLengthText();
    summaryHtml += getRadioText("topType", "Top Fitting");
    summaryHtml += getRadioText("endType", "End Fitting");
    summaryHtml += getCheckboxStatus();
    summaryHtml += getSelectText("tcOrder", "Order");
    summaryHtml += getSelectText("turnbuckleSize", "TB Size");
    summaryHtml += getSelectText("chainLength", "Chain Length");

    summaryHtml += '</div>';

    if (summaryHtml === '<div class="space-y-4"></div>') {
        $summaryBox.html('<p class="text-xs text-slate-400 text-center italic">Selection preview will appear here</p>');
    } else {
        $summaryBox.html(summaryHtml);
    }

}

//toggle function for accordina in order
function toggle(btn) {
    const content = btn.nextElementSibling;
    const icon = btn.querySelector('.chevron');  // ← target chevron specifically
    const isOpen = !content.classList.contains('hidden');

    document.querySelectorAll('.accordion-btn').forEach(b => {
        b.nextElementSibling.classList.add('hidden');
        b.querySelector('.chevron').classList.remove('rotate-180');  // ← here too
    });

    if (!isOpen) {
        content.classList.remove('hidden');
        icon.classList.add('rotate-180');
    }
}

// --- Common Delete Modal Logic (modal.html) --- //

let _pendingDeleteCallback = null;

function showDeleteModal(itemName, onConfirm) {
    _pendingDeleteCallback = onConfirm;
    $('#deleteModalItemName').text('"' + itemName + '"');
    $('#deleteModalConfirm')
        .prop('disabled', false)
        .html(`
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7
                         m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            Remove
        `);
    $('#deleteModal').removeClass('hidden').addClass('flex');
    requestAnimationFrame(function () {
        $('#deleteModalBackdrop').css('opacity', '1');
        $('#deleteModalCard').css({ opacity: '1', transform: 'scale(1)' });
    });
    setTimeout(function () { $('#deleteModalCancel').focus(); }, 50);
}

function closeDeleteModal() {
    $('#deleteModalBackdrop').css('opacity', '0');
    $('#deleteModalCard').css({ opacity: '0', transform: 'scale(0.95)' });
    setTimeout(function () {
        $('#deleteModal').removeClass('flex').addClass('hidden');
        _pendingDeleteCallback = null;
    }, 200);
}

// Sets the confirm button to a loading spinner
function setDeleteModalLoading() {
    $('#deleteModalConfirm').prop('disabled', true).html(`
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        Removing…`);
}

// --- Cart-specific delete --- //
function deleteItem(event, el) {
    event.stopPropagation();
    const orderId  = el.dataset.orderId;
    const card     = el.closest('.accordion-item');
    const itemName = card.querySelector('.font-semibold.text-slate-800').textContent.trim();

    showDeleteModal(itemName, function () {
        setDeleteModalLoading();
        ajaxDelete('/customer/cart/delete/' + orderId + '/', 
            function onSuccess() {
                closeDeleteModal();
                card.remove();
                const remaining = $('.accordion-item').length;
                if (remaining === 0) {
                    $('#emptyCartMsgId').removeClass('hidden');
                    $('#cartCountId').text('0 Items');
                    $('#btnSubmitId').addClass('hidden');
                } else {
                    $('#cartCountId').text(remaining + ' Item' + (remaining !== 1 ? 's' : ''));
                }
                showNotification('"' + itemName + '" removed from cart.', 'warning');
            },
            function onError(response) {
                closeDeleteModal();
                showNotification(response.message || 'Could not delete item.', 'error');
            }
        );
    });
}

// --- Dashboard-specific delete --- //
function confirmOrderDelete(orderId, orderName) {
    showDeleteModal(orderName, function () {
        setDeleteModalLoading();
        ajaxDelete('/customer/order/' + orderId + '/delete/',
            function onSuccess() {
                closeDeleteModal();

                // Find row by data attribute — reliable match
                const $row = $('tr[data-order-id="' + orderId + '"]');

                if ($row.length) {
                    $row.fadeOut(300, function () {
                        $(this).remove();
                        const remaining = $('tbody tr').not(':has(td[colspan])').length;
                        if (remaining === 0) {
                            $('tbody').html(
                                '<tr>' +
                                    '<td colspan="6" class="py-20 text-center">' +
                                        '<p class="text-slate-400 text-sm">No orders found.</p>' +
                                    '</td>' +
                                '</tr>'
                            );
                        }
                        $('span.text-xs.text-slate-400').text(remaining + ' total records');
                    });
                }

                showNotification('"' + orderName + '" Deleted.');
            },
            function onError(response) {
                closeDeleteModal();
                showNotification(response.message || 'Could not delete order.', 'error');
            }
        );
    });
}

// --- End Delete Model Logic --- //

// Open order details in model
function openDetailModal(id) {
    $('#detailModal').removeClass('hidden').hide().fadeIn(200).css('display', 'flex');
    $('body').css('overflow', 'hidden');
    $('#detailContent').addClass('opacity-50');

    $.ajax({
        url: `/customer/order/${id}/detail/`,
        type: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
            $('#m_name').text(data.orderName);
            $('#m_deliverBy').text(data.deliverBy || 'N/A');
            $('#m_quantity').text(data.quantity);
            $('#m_size').text(data.cableSize);
            $('#m_finish').text(data.cableFinishes);

            var parts = [];
            if (data.cableLengthFt && parseInt(data.cableLengthFt) > 0) parts.push(data.cableLengthFt + "'");
            if (data.cableLengthIn && parseInt(data.cableLengthIn) > 0) parts.push(data.cableLengthIn + '"');
            $('#m_cableLength').text(parts.length > 0 ? parts.join(' ') : 'N/A');

            $('#m_top').text(data.topType);
            $('#m_end').text(data.endType);
            $('#m_tc').text(data.tcOrder || 'N/A');
            $('#m_tbsize').text(data.turnbuckleSize || 'N/A');
            $('#m_chainLength').text(data.chainLength || 'N/A');

            $('#detailContent').removeClass('opacity-50');
        },
        error: function(xhr) {
            closeModal();
            showNotification('Could not load order details.', 'error');
        }
    });
}

// Close modal of order details
function closeModal() {
    $('#detailModal').fadeOut(200, function() {
        $(this).addClass('hidden');
        $('body').css('overflow', 'auto');
    });
}

// --- Cable Length Warning Modal Start --- //
let _skipCableLengthCheck = false;

function showCableLengthWarning(msg) {
    $('#cableLengthWarningMsg').text(msg);
    $('#cableLengthWarningModal').removeClass('hidden');
    requestAnimationFrame(function() {
        $('#cableLengthWarningBackdrop').css('opacity', '1');
        $('#cableLengthWarningCard').css({ opacity: '1', transform: 'scale(1)' });
    });
}

function closeCableLengthWarning() {
    $('#cableLengthWarningBackdrop').css('opacity', '0');
    $('#cableLengthWarningCard').css({ opacity: '0', transform: 'scale(0.95)' });
    setTimeout(function() {
        $('#cableLengthWarningModal').addClass('hidden');
    }, 200);
}

function setupCableLengthWarning() {
    var $ft = $('input[name="cableLengthFt"]');
    var $in = $('input[name="cableLengthIn"]');
    var $approved = $('#cableLengthApproved');

    if ($ft.length === 0) return;

    function checkCableLength() {
        var ft = parseInt($ft.val()) || 0;
        var inches = parseInt($in.val()) || 0;
        var totalInches = (ft * 12) + inches;

        if (totalInches >= 840) {
            $approved.val('false');
            showCableLengthWarning(
                'The cable length you entered is ' + ft + '\' ' + inches + '" (' + totalInches + ' inches total). ' +
                'This exceeds 70 feet. Are you sure this is correct?'
            );
        } else {
            $approved.val('true');
        }
    }

    $ft.on('change input', checkCableLength);
    $in.on('change input', checkCableLength);

    // User confirms — just set the flag and close
    $('#cableLengthWarningConfirm').on('click', function() {
        $approved.val('true');
        closeCableLengthWarning();
    });

    // User cancels — reset values and close
    $('#cableLengthWarningCancel, #cableLengthWarningBackdrop').on('click', function() {
        $approved.val('false');
        $ft.val('0');
        $in.val('0');
        closeCableLengthWarning();
        updateSummary();
    });
}
// --- Cable Length Warning Modal End --- //


// --- Filter Order Start --- //

function applyFilters() {
    var show = $('#filterShow').val();
    var deliverBy = $('#filterDate').val();

    $.ajax({
        url: '/customer/orders/filter/',
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        contentType: 'application/json',
        data: JSON.stringify({
            show: show,
            deliverBy: deliverBy
        }),
        beforeSend: function() {
            $('tbody').html(
                '<tr><td colspan="8" class="py-20 text-center">' +
                '<i class="fa-solid fa-circle-notch fa-spin text-emerald-500 text-xl"></i>' +
                '<p class="text-slate-400 text-sm mt-2">Filtering...</p>' +
                '</td></tr>'
            );
        },
        success: function(response) {
            var orders = response.orders;
            var canChange = response.can_change;
            var canDelete = response.can_delete;
            $('span.text-xs.text-slate-400').text(response.count + ' total records');

            if (orders.length === 0) {
                $('tbody').html(
                    '<tr><td colspan="8" class="py-20 text-center">' +
                    '<p class="text-slate-400 text-sm">No orders found.</p>' +
                    '</td></tr>'
                );
                return;
            }

            var html = '';
            orders.forEach(function(order) {
                var statusClass = '';
                if (order.status === 'Placed') statusClass = 'bg-emerald-100 text-emerald-700';
                else if (order.status === 'Draft') statusClass = 'bg-amber-100 text-amber-700';
                else statusClass = 'bg-slate-100 text-slate-600';

                html += '<tr data-order-id="' + order.orderId + '" class="hover:bg-slate-50 transition-colors">';
                html += '<td class="px-6 py-4 text-xs font-mono text-slate-400">#' + order.orderIdShort + '</td>';
                html += '<td class="px-6 py-4">';
                html += '<button type="button" onclick="openDetailModal(\'' + order.orderId + '\')" ';
                html += 'class="text-sm font-semibold text-slate-800 hover:text-emerald-600 transition-colors text-left underline decoration-dotted">';
                html += order.orderName + '</button></td>';
                html += '<td class="px-6 py-4 text-sm text-slate-600">' + order.customerName + '</td>';
                html += '<td class="px-6 py-4 text-sm text-slate-600">' + order.showName + '</td>';
                html += '<td class="px-6 py-4 text-sm text-slate-600">' + order.orderedDate + '</td>';
                html += '<td class="px-6 py-4 text-sm text-slate-600">' + order.deliverBy + '</td>';
                html += '<td class="px-6 py-4 text-sm text-center font-medium">' + order.quantity + '</td>';
                html += '<td class="px-6 py-4 text-center">';
                html += '<span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase ' + statusClass + '">' + order.status + '</span></td>';
                html += '<td class="px-6 py-4 text-center"><div class="flex items-center justify-center gap-2">';

                if (canChange) {
                    html += '<button type="button" onclick="openEditModal(\'' + order.orderId + '\')" ';
                    html += 'class="inline-flex items-center justify-center p-2 rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors">';
                    html += '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" class="w-4 h-4 fill-current"><path d="M505 122.9L517.1 135C526.5 144.4 526.5 159.6 517.1 168.9L488 198.1L441.9 152L471 122.9C480.4 113.5 495.6 113.5 504.9 122.9zM273.8 320.2L408 185.9L454.1 232L319.8 366.2C316.9 369.1 313.3 371.2 309.4 372.3L250.9 389L267.6 330.5C268.7 326.6 270.8 323 273.7 320.1zM437.1 89L239.8 286.2C231.1 294.9 224.8 305.6 221.5 317.3L192.9 417.3C190.5 425.7 192.8 434.7 199 440.9C205.2 447.1 214.2 449.4 222.6 447L322.6 418.4C334.4 415 345.1 408.7 353.7 400.1L551 202.9C579.1 174.8 579.1 129.2 551 101.1L538.9 89C510.8 60.9 465.2 60.9 437.1 89zM152 128C103.4 128 64 167.4 64 216L64 488C64 536.6 103.4 576 152 576L424 576C472.6 576 512 536.6 512 488L512 376C512 362.7 501.3 352 488 352C474.7 352 464 362.7 464 376L464 488C464 510.1 446.1 528 424 528L152 528C129.9 528 112 510.1 112 488L112 216C112 193.9 129.9 176 152 176L264 176C277.3 176 288 165.3 288 152C288 138.7 277.3 128 264 128L152 128z"/></svg>';
                    html += '</button>';
                }

                if (canDelete) {
                    html += '<button type="button" onclick="confirmOrderDelete(\'' + order.orderId + '\', \'' + order.orderName.replace(/'/g, "\\'") + '\')" ';
                    html += 'class="inline-flex items-center justify-center p-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 transition-colors">';
                    html += '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" class="w-4 h-4 fill-current"><path d="M262.2 48C248.9 48 236.9 56.3 232.2 68.8L216 112L120 112C106.7 112 96 122.7 96 136C96 149.3 106.7 160 120 160L520 160C533.3 160 544 149.3 544 136C544 122.7 533.3 112 520 112L424 112L407.8 68.8C403.1 56.3 391.2 48 377.8 48L262.2 48zM128 208L128 512C128 547.3 156.7 576 192 576L448 576C483.3 576 512 547.3 512 512L512 208L464 208L464 512C464 520.8 456.8 528 448 528L192 528C183.2 528 176 520.8 176 512L176 208L128 208zM288 280C288 266.7 277.3 256 264 256C250.7 256 240 266.7 240 280L240 456C240 469.3 250.7 480 264 480C277.3 480 288 469.3 288 456L288 280zM400 280C400 266.7 389.3 256 376 256C362.7 256 352 266.7 352 280L352 456C352 469.3 362.7 480 376 480C389.3 480 400 469.3 400 456L400 280z"/></svg>';
                    html += '</button>';
                }

                if (!canChange && !canDelete) {
                    html += '<span class="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-400">View Only</span>';
                }

                html += '</div></td></tr>';
            });

            $('tbody').html(html);
        },
        error: function() {
            showNotification('Could not filter orders.', 'error');
        }
    });
}

// --- Filter Order End --- //

// --- Taildown Preview Start --- //

/* ============================ CONSTANTS ============================ */
var mdl = document.getElementById('previewModal');

var IMG = {
  CROSBY:     mdl.dataset.imgCrosby     || '',
  NICO:       mdl.dataset.imgNico       || '',
  SOFT_EYE:   mdl.dataset.imgSoftEye    || '',
  HARD_EYE:   mdl.dataset.imgHardEye    || '',
  TURNBUCKLE: mdl.dataset.imgTurnbuckle || '',
  CHAIN:      mdl.dataset.imgChain      || ''
};

var TC_LABELS = {
    'OT': 'Only Turnbuckle', 'OC': 'Only Chain',
    'TC': 'Turnbuckle then Chain', 'CT': 'Chain then Turnbuckle',
    'none': 'None'
};

var Finishies = {
    'GAL': 'Galvanized',
    'BLK': 'Blackened',
}

var COLORS = {
    emerald: { border: '#a7f3d0', text: '#065f46' },
    amber:   { border: '#fde68a', text: '#92400e' },
    orange:  { border: '#fed7aa', text: '#9a3412' },
    slate:   { border: '#e2e8f0', text: '#334155' }
};

/* ============================ UTILITY FUNCTIONS ============================ */

function val(v) {
    if (!v || v === 'None' || v === 'none' || v === 'undefined' || v === 'null') return '';
    return v.trim();
}

function isTruthy(v) {
    return v === 'True' || v === 'true' || v === '1';
}

function getColor(name, type) {
    return (COLORS[name] || COLORS.slate)[type];
}

function getTopImg(topType) {
    if (topType === 'Soft Eye') return IMG.SOFT_EYE;
    if (topType === 'Hard Eye') return IMG.HARD_EYE;
    return null;
}

function getEndImg(endType) {
    if (!endType) return null;
    var t = endType.toLowerCase();
    if (t === 'crosby') return IMG.CROSBY;
    if (t === 'nico') return IMG.NICO;
    return null;
}

function $(id) { return document.getElementById(id); }

/* ============================ DATA EXTRACTION & VALIDATION ============================ */

function extractData(dataset) {
    var d = dataset;
    var hasTb = isTruthy(d.turnbuckle);
    var hasCh = isTruthy(d.chain);
    var ft = val(d.cableLengthFt) || '0';
    var inches = val(d.cableLengthIn) || '0';
    var tcOrder = val(d.tcOrder) || 'none';

    return {
        orderName:     val(d.orderName) || 'Untitled Order',
        quantity:      val(d.quantity) || '1',
        showName:      val(d.showName),
        deliverBy:     val(d.deliverBy),
        topType:       val(d.topType),
        endType:       val(d.endType),
        cableSize:     val(d.cableSize),
        cableFinishes: Finishies[val(d.cableFinishes)] || val(d.cableFinishes),
        cableLength:   ft + "' " + inches + '"',
        hasTb:         hasTb,
        hasCh:         hasCh,
        tcOrder:       tcOrder,
        tcOrderLabel:  TC_LABELS[tcOrder] || tcOrder,
        tbSize:        hasTb ? val(d.turnbuckleSize) : '',
        chainLen:      hasCh ? val(d.chainLength) : ''
    };
}

/* ============================ HEADER BUILDER ============================ */

function createBadge(text, bgClass, textClass, borderClass) {
    var badge = document.createElement('span');
    badge.className = 'px-2 py-0.5 text-[10px] sm:text-xs font-semibold rounded-full border ' + bgClass + ' ' + textClass + ' ' + borderClass;
    badge.textContent = text;
    return badge;
}

function buildHeader(data) {
    $('previewTitle').textContent = data.orderName;

    var badges = $('headerBadges');
    badges.innerHTML = '';

    badges.appendChild(createBadge('Qty: ' + data.quantity, 'bg-emerald-50', 'text-emerald-700', 'border-emerald-200'));

    if (data.showName) {
        badges.appendChild(createBadge(data.showName, 'bg-blue-50', 'text-blue-700', 'border-blue-200'));
    }
    if (data.deliverBy) {
        badges.appendChild(createBadge('Due: ' + data.deliverBy, 'bg-violet-50', 'text-violet-700', 'border-violet-200'));
    }
}

/* ============================ DETAILS GRID BUILDER ============================ */

function createDetailCell(label, value) {
    var cell = document.createElement('div');

    var lbl = document.createElement('p');
    lbl.className = 'text-[10px] sm:text-xs text-slate-400 uppercase tracking-wider font-medium mb-0.5';
    lbl.textContent = label;

    var v = document.createElement('p');
    v.className = 'text-sm sm:text-base lg:text-lg font-semibold text-slate-700';
    v.textContent = value || '—';

    cell.appendChild(lbl);
    cell.appendChild(v);
    return cell;
}

function buildDetailsGrid(data) {
    var grid = $('detailsGrid');
    grid.innerHTML = '';

    grid.appendChild(createDetailCell('Cable Size', data.cableSize));
    grid.appendChild(createDetailCell('Cable Finish', data.cableFinishes));
    grid.appendChild(createDetailCell('Cable Length', data.cableLength));
    grid.appendChild(createDetailCell('Top Fitting', data.topType || 'None'));
    grid.appendChild(createDetailCell('End Fitting', data.endType || 'None'));

    if (data.hasTb || data.hasCh) {
        grid.appendChild(createDetailCell('Hardware Order', data.tcOrderLabel));
    }
    if (data.hasTb && data.tbSize) {
        grid.appendChild(createDetailCell('Turnbuckle Size', data.tbSize));
    }
    if (data.hasCh && data.chainLen) {
        grid.appendChild(createDetailCell('Chain Length', data.chainLen));
    }
}

/* ============================ ASSEMBLY DIAGRAM BUILDER ============================ */

function createPartCard(imgSrc, label, detail, color) {
    var wrapper = document.createElement('div');
    wrapper.className = 'flex flex-col items-center text-center w-full';

    var imgBox = document.createElement('div');
    imgBox.className = 'relative w-28 h-32 sm:w-32 sm:h-40 lg:w-36 lg:h-44 flex items-center justify-center rounded-xl border-2 bg-white shadow-sm overflow-hidden p-3';
    imgBox.style.borderColor = getColor(color, 'border');

    if (imgSrc) {
        var img = document.createElement('img');
        img.src = imgSrc;
        img.alt = label;
        img.className = 'max-w-full max-h-full object-contain';
        imgBox.appendChild(img);
    } else {
        var ph = document.createElement('span');
        ph.className = 'text-slate-300 text-xs sm:text-sm';
        ph.textContent = 'No Image';
        imgBox.appendChild(ph);
    }

    var textGroup = document.createElement('div');
    textGroup.className = 'mt-2 sm:mt-3 px-2';

    var title = document.createElement('p');
    title.className = 'text-sm sm:text-base lg:text-lg font-bold leading-tight';
    title.style.color = getColor(color, 'text');
    title.textContent = label;
    textGroup.appendChild(title);

    if (detail) {
        var sub = document.createElement('p');
        sub.className = 'text-xs sm:text-sm lg:text-base text-slate-400 mt-0.5 font-medium';
        sub.textContent = detail;
        textGroup.appendChild(sub);
    }

    wrapper.appendChild(imgBox);
    wrapper.appendChild(textGroup);
    return wrapper;
}

function createConnector() {
    var div = document.createElement('div');
    div.className = 'flex flex-col items-center py-0.5 sm:py-1';
    div.innerHTML = '<div class="w-0.5 h-5 sm:h-6 lg:h-8 bg-slate-200 rounded-full"></div>';
    return div;
}

function getHardwareParts(data) {
    var parts = [];
    if (data.tcOrder === 'TC' && data.hasTb && data.hasCh) {
        parts.push({ img: IMG.TURNBUCKLE, label: 'Turnbuckle', detail: data.tbSize, color: 'amber' });
        parts.push({ img: IMG.CHAIN, label: 'Chain', detail: data.chainLen, color: 'orange' });
    } else if (data.tcOrder === 'CT' && data.hasTb && data.hasCh) {
        parts.push({ img: IMG.CHAIN, label: 'Chain', detail: data.chainLen, color: 'orange' });
        parts.push({ img: IMG.TURNBUCKLE, label: 'Turnbuckle', detail: data.tbSize, color: 'amber' });
    } else if (data.hasTb) {
        parts.push({ img: IMG.TURNBUCKLE, label: 'Turnbuckle', detail: data.tbSize, color: 'amber' });
    } else if (data.hasCh) {
        parts.push({ img: IMG.CHAIN, label: 'Chain', detail: data.chainLen, color: 'orange' });
    }
    return parts;
}

function buildAssemblyDiagram(data) {
    var container = $('assemblyDiagram');
    container.innerHTML = '';

    var parts = [];

    // 1. Top (always)
    parts.push({ img: getTopImg(data.topType), label: 'Top: ' + (data.topType || 'None'), detail: null, color: 'emerald' });

    // 2. End (always)
    parts.push({ img: getEndImg(data.endType), label: 'End: ' + (data.endType || 'None'), detail: null, color: 'slate' });

    // 3. Hardware (conditional, validated)
    var hw = getHardwareParts(data);
    for (var j = 0; j < hw.length; j++) { parts.push(hw[j]); }

    // Render
    for (var i = 0; i < parts.length; i++) {
        container.appendChild(createPartCard(parts[i].img, parts[i].label, parts[i].detail || null, parts[i].color));
        if (i < parts.length - 1) {
        container.appendChild(createConnector());
        }
    }
}

/* ============================ MODAL CONTROLLER ============================ */

function resetModal() {
    $('previewTitle').textContent = '';
    $('headerBadges').innerHTML = '';
    $('detailsGrid').innerHTML = '';
    $('assemblyDiagram').innerHTML = '';
}

function openPreview(btn) {
    resetModal();
    var data = extractData(btn.dataset);
    buildHeader(data);
    buildDetailsGrid(data);
    buildAssemblyDiagram(data);
    $('previewModal').classList.remove('hidden');
}

function closePreview() {
    $('previewModal').classList.add('hidden');
}

/* ============================ EVENT LISTENERS ============================ */

$('previewBackdrop').addEventListener('click', closePreview);
$('previewCloseBtn').addEventListener('click', closePreview);
$('previewDoneBtn').addEventListener('click', closePreview);

document.addEventListener('click', function(e) {
    var btn = e.target.closest('.preview-btn');
    if (btn) {
        e.preventDefault();
        e.stopPropagation();
        openPreview(btn);
    }
});

// --- Taildown Preview End --- //

//Load logic in DOM
$(document).ready(function() {

    //Render any Django flash messages (success / error / warning) as toast notifications.
    //Messages are embedded in the HTML as data attributes to avoid inline JS.
    $("#django-messages .message-data").each(function() {
        showNotification($(this).data("text"), $(this).data("tag"));
    });

    //A single delegated listener on the form covers all current and future inputs.
    //Both handlers are intentionally separate so each has a single responsibility.
    $('form').on('change', 'input, select', function() {
        updateSummary();
    });

    $('form').on('change', 'input, select', function() {
        handleHardwareLogic();
    });

    //Spinner
    $('form').on('submit', function(e) {
        $('#loading-overlay').removeClass('hidden').addClass('flex');             
    });

    $(window).on('pageshow', function() {
        $('#loading-overlay').addClass('hidden');
    });

    //Force the browser forward when 'back' is clicked
    window.history.pushState(null, null, window.location.href);
    $(window).on('popstate', function() {
        window.history.go(1);
    });

    // Toggle chain length / TB size visibility in edit modal
    $('#editModal').on('change', '#edit_turnbuckle', function() {
        if ($(this).is(':checked')) {
            $('#edit_turnbuckleSize').closest('.edit-field-group').show();
        } else {
            $('#edit_turnbuckleSize').closest('.edit-field-group').hide().find('select').val('');
        }
    });

    $('#editModal').on('change', '#edit_chain', function() {
        if ($(this).is(':checked')) {
            $('#edit_chainLength_group').show();
        } else {
            $('#edit_chainLength_group').hide().find('select').val('');
        }
    });

    //Run both once on page load to reflect any server-side pre-filled values
    updateSummary();
    handleHardwareLogic();
    setupCableLengthWarning();

    // ── Delete Modal Button Handlers ──────────────────────────────────────────

    $('#deleteModalConfirm').on('click', function () {
        console.log('=== CONFIRM BUTTON CLICKED ===');
        if (typeof _pendingDeleteCallback === 'function') {
            _pendingDeleteCallback();
        }
    });
    $('#deleteModalCancel, #deleteModalBackdrop').on('click', closeDeleteModal);

    // Edit
    $('#editModal').on('change', '#edit_chain', function() {
        if ($(this).is(':checked')) {
            $('#edit_chainLength_group').show();
        } else {
            $('#edit_chainLength_group').hide().find('select').val('');
        }
    });

    //filter
    $('#btnApplyFilter').on('click', function() {
        applyFilters();
    });

    $('#btnClearFilter').on('click', function() {
        $('#filterShow').val('');
        $('#filterDate').val('');
        applyFilters();
    });

});