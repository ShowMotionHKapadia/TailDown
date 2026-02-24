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
        duration: 30000,
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

//Controls two pieces of conditional UI based on the hardware checkbox state:
//1.Turnbuckle Size selector — shown/enabled only when the turnbuckle is checked.
//2.Order dropdown options — filtered so only valid combinations are visible.
function handleHardwareLogic() {
    const isTB = $('input[name="turnbuckle"]').is(':checked');
    const isChain = $('input[name="chain"]').is(':checked');
    
    const $orderSelect = $('select[name="tcOrder"]');
    const $sizeSelect = $('select[name="turnbuckleSize"]');
    const $sizeContainer = $sizeSelect.closest('.flex-1');

    //Show the TB size field only when a turnbuckle is part of the order
    if (isTB) {
        $sizeContainer.show(); // Matches requirements: Show TB size
        $sizeSelect.prop('disabled', false);
    } else {
        //Hide and disable so the empty value is not accidentally submitted
        $sizeContainer.hide(); //Matches requirements: Hide TB size
        $sizeSelect.prop('disabled', true).val("");
    }

    //Reset all options to hidden first, then reveal only the valid ones
    $orderSelect.find('option').hide(); 
    $orderSelect.find('option[value=""]').show(); //Placeholder
    $orderSelect.find('option[value="none"]').show(); //Always show "None" by default

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
        $orderSelect.val('none');
    }

    updateSummary();
}


//Rebuilds the Order Summary panel in the aside from the current form field values.
//Shows a placeholder message if no fields have been filled in yet.
function updateSummary() {

    //Re-query the summary container each call in case the DOM has been re-rendered
    const $summaryBox = $('aside .slim-scroll'); 
    if ($summaryBox.length === 0) return;

    let summaryHtml = '<div class="space-y-4">';

    //Collect each field's current value; helpers return "" if the field is empty
    summaryHtml += getInputText("orderName", "Order Name");
    summaryHtml += getInputText("quantity", "Quantity");
    summaryHtml += getSelectText("showName", "Show");
    summaryHtml += getSelectText("cableFinishes", "Finish");
    summaryHtml += getSelectText("cableSize", "Cable Size");
    summaryHtml += getRadioText("topType", "Top Fitting");
    summaryHtml += getRadioText("endType", "End Fitting");
    summaryHtml += getCheckboxStatus();
    summaryHtml += getSelectText("tcOrder", "Order");
    summaryHtml += getSelectText("turnbuckleSize", "TB Size");

    summaryHtml += '</div>';

    if (summaryHtml === '<div class="space-y-4"></div>') {
        $summaryBox.html('<p class="text-xs text-slate-400 text-center italic">Selection preview will appear here</p>');
    } else {
        $summaryBox.html(summaryHtml);
    }

}

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

    //Run both once on page load to reflect any server-side pre-filled values
    updateSummary();
    handleHardwareLogic();
});