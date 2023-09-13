//Embellish putts
var updatedHoles = [];
var updateHoles;
var nextHole;
$(document).on('focus', 'input[type=tel]', function (el, e) {
    var that = this;
    setTimeout(function () { $(that).select(); }, 10);
});
var lastRoundDetails;
var quickEmellish = function (el, e) {

    var k, h, p;
    if (document.all) {
        k = e.keyCode;
    } else {
        k = e.which;
    }
    el = $(el);
    if (k == 46) {
        el.value = '';
        e.returnValue = false;
        return;
    }
    if (k == 8) {
        e.returnValue = false;
        return;
    }
    if (k == 37) {
        e.returnValue = false;
        return;
    }
    if (k == 39) {
        e.returnValue = false;
        return;
    }

    //Next holeSS number
    h = parseInt(el.attr("data-putts-hole")) + 1;

    p = el.parent().parent().parent();

    var nh = p.find("[data-putts-hole='" + h + "']");

    nextHole = nh;
    //andriod chrome
    if (k === 229) {
        e.returnValue = false;
        updatedHoles.push({ RoundId: parseInt(p.attr("data-rounddetails")), HoleNo: h - 1, Putts: parseInt(el.val()), Embellish: "" });
        setTimeout(function () {
            nextHole.focus().select();
        }, 300);
    }
    else {


        //normal keys
        if (k > 47 && k < 58) {
            el.val(k - 48);
            updatedHoles.push({ RoundId: parseInt(p.attr("data-rounddetails")), HoleNo: h - 1, Putts: parseInt(el.val()), Embellish: "" });
            nh.focus().select();
        } else if (k > 95 && k < 106) //number pad
        {
            el.val(k - 96);
            updatedHoles.push({ RoundId: parseInt(p.attr("data-rounddetails")), HoleNo: h - 1, Putts: parseInt(el.val()), Embellish: "" });
            nh.focus().select();
        }
    }
    e.returnValue = false;
    e.preventDefault();
    lastRoundDetails = p;
    var check = p.find("[data-putts-hole='19']");
    check.html("<i class='fa fa-pencil text-primary'></i>");
    sumPutts(p);


    if (updatedHoles.length > 0) {
       
        clearTimeout(updateHoles);
        
        var saveIn = 5000;

        if (h === 19) saveIn = 1000;
        updateHoles = setTimeout(function() {
            submitEmbelish('updatePutts');
        }, saveIn);
    }
};


var sumPutts = function (round) {

    var total = 0;

    round.find("[data-putts-hole]").each(function () {
        var el = $(this);
        var h = el.attr("data-putts-hole");

        if (h < 19) {
            total += parseInt(el.val());
        }

    });

    if (total >= 0) round.find(".total-putts strong").text(total);


}

//Submit the embellish data to be saved
var submitEmbelish = function (updateType) { // Send the request
    
    var check = lastRoundDetails.find(".fa-pencil");
    check.parent().html("<i class='fa fa-circle-o-notch fa-spin'></i>");

    $.ajax({
        url: updateType,
        type: 'POST',
        data: JSON.stringify(updatedHoles),
        dataType: 'json',
        contentType: 'application/json',
        xhrFields: {
            withCredentials: true
        },
        success: function(response) {
            // Do something with the request
            updatedHoles = [];
            var round = JSON.parse(response);

            //Update the stats data if it exists
            if ("allData" in window) {

                //remove the updated round
                allData = allData.filter(function(el) {
                    return el.Id !== round.Id;
                });

                //reAdd the round
                allData.push(round);
                if ("filterStatsData" in window) {
                    filterStatsData();
                }
                if ("updateOverview" in window) {
                    updateOverview();
                }

            }

            //Confirm the save
            var check = lastRoundDetails.find("[data-putts-hole='19']");
            check.html("<i class='fa fa-check text-success'></i>");

            bootler.notify({
                type: "success",
                containerType: "right",
                msg: "Your embellishment has been saved.",
                closeable: false,
                autoDismiss: true,
                onDismiss: function () { }
            });
        },
        error: function(response) {
            
            bootler.notify({
                type: "error",
                containerType: "right",
                msg: JSON.parse(response.responseText),
                closeable: false,
                autoDismiss: true,
                onDismiss: function() {}
            });
        }
    });

}

//scroll fix for andriod
if (/Android/.test(navigator.appVersion)) {
    window.addEventListener("resize", function () {
        if (document.activeElement.tagName == "INPUT") {
            window.setTimeout(function () {
                document.activeElement.scrollIntoViewIfNeeded();
            }, 1000);
        }
    });
}

//Update the selected value to include the optgroup
$('body').on("change", 'select.shot', (function () {
    var self = $(this);
    var opt = self.find(':selected');
    var sel = opt.text();
    var val = opt.val();
    var og = opt.closest('optgroup').attr('label');
    if (og == undefined) { og = ''; } else { og = og + ' to '; }
    self.find('option:not(disabled)').each(function () {

        var el = $(this);
        var sel = el.text();
        var og = el.closest('optgroup').attr('label');
        el.text(sel.replace(og + ' to ', ''));
    });

    $(this).find(':selected').text(og + sel);
    
    if ("37*+".includes(val)) {
        // we are on the green set all remaing shots to puts

        self.parent().parent().nextAll().find('select').each(function() {
            self = $(this);
            self.empty();
            self.append($('<option disabled selected value=" "> Please Select </option>\
            <optgroup label="Wood">\
                <option value="1">Fairway</option>\
                <option value="2">Rough</option>\
                <option value="3">Green</option>\
                <option value="4">Bunker</option>\
            </optgroup>\
            <optgroup label="Iron">\
                <option value="5">Fairway</option>\
                <option value="6">Rough</option>\
                <option value="7">Green</option>\
                <option value="8">Bunker</option>\
            </optgroup>\
            <optgroup label="Chip">\
                <option value="9">Fairway</option>\
                <option value="/">Rough</option>\
                <option value="*">Green</option>\
                <option value="-">Bunker</option>\
            </optgroup>\
            <option value="0">Penalty</option>\
            <option selected value="+">Putt</option>'));
        });
    }

    
    //Save the change
    var embellishTab = self.closest('.tab-pane');
    var roundId = parseInt(embellishTab.attr('id').replace('embellish_', ""));
    //Find the round
    var round = allData.filter(function (el) {
        return el.Id === roundId;
    });
    var shots = embellishTab.find('.shots');
    updateInfo(round, shots);

    //hole has changed so delay the save
    if (updatedHoles.length > 0) {

        clearTimeout(updateHoles);
       
        updateHoles = setTimeout(function () {
            submitEmbelish('updateHoles');
        }, 5000);
    }
}));


$('body').on("click", ".selectHole1", function () {

    var self = $(this);

    self.parent().parent().parent().find('.holes option[value="1"]').prop('selected', true).change();

});
//move to the next hole for embellishment
$('body').on("click", ".hole-change.next", function () {
    var self = $(this);
    var hole = parseInt(self.parent().parent().find('.holes :selected').val());
    hole += 1;
    if (hole >= 19) hole = 1;
    self.parent().parent().parent().find('.holes option[value="' + hole + '"]').prop('selected', true).change();
    });

//move to the previous hole for embellishment
$('body').on("click", ".hole-change.previous", function () {
    var self = $(this);
    var hole = parseInt(self.parent().parent().find('.holes :selected').val());
    hole -= 1;
    if (hole <= 0) hole = 18;
    self.parent().parent().parent().find('.holes option[value="' + hole + '"]').prop('selected', true).change();
    });

//Update the shots when the hole changes
$('body').on("change", "select.holes", function () {
    //Find the embelish info for this hole 
    var self = $(this);
    
    var embellishTab = self.closest('.tab-pane');
    var roundId = parseInt(embellishTab.attr('id').replace('embellish_', ""));
    lastRoundDetails = embellishTab.parent().parent();
    //Find the round
    var round = allData.filter(function (el) {
        return el.Id === roundId;
    });

    var opt = self.find(':selected');
    var hole = opt.val();

    var embellishInfo = round[0].RoundHoleDetailSummaries[hole - 1].E;
    var shots = embellishTab.find('.shots');

    //Are there any shots if so lets save them back to the js data
    //if (shots.find('select :selected').length > 0) {updateInfo(round,shots);}

    //Clear down the shots for the next hole
    shots.empty();

    if (embellishInfo == null || embellishInfo.length === 0) {
        embellishInfo = new Array(round[0].RoundHoleDetailSummaries[hole - 1].G + 1 ).join(" ");
    }

    //Add a select for each shot
    for (var i = 0; i < embellishInfo.length; i++) {

        var shot = embellishInfo.substring(i, i + 1);
        shots.append('<li class="custom"> <div class="input-group" style="width: 100%;">\
            <span class="input-group-addon " style="width:35px;">' + (i + 1) + '</span></span>\
            <select  data-hole="' + hole + '" data-shot=' + i + ' class="form-control shot" >\
            <option disabled selected value=" "> Please Select </option>\
            <optgroup label="Wood">\
                <option ' + ((shot === "1") ? "selected" : "") + ' value="1">' + ((shot === "1") ? "Wood to " : "") + ' Fairway</option>\
                <option ' + ((shot === "2") ? "selected" : "") + ' value="2">' + ((shot === "2") ? "Wood to " : "") + ' Rough</option>\
                <option ' + ((shot === "3") ? "selected" : "") + ' value="3">' + ((shot === "3") ? "Wood to " : "") + ' Green</option>\
                <option ' + ((shot === "4") ? "selected" : "") + ' value="4">' + ((shot === "4") ? "Wood to " : "") + ' Bunker</option>\
            </optgroup>\
            <optgroup label="Iron">\
                <option ' + ((shot === "5") ? "selected" : "") + ' value="5">' + ((shot === "5") ? "Iron to " : "") + ' Fairway</option>\
                <option ' + ((shot === "6") ? "selected" : "") + ' value="6">' + ((shot === "6") ? "Iron to " : "") + ' Rough</option>\
                <option ' + ((shot === "7") ? "selected" : "") + ' value="7">' + ((shot === "7") ? "Iron to " : "") + ' Green</option>\
                <option ' + ((shot === "8") ? "selected" : "") + ' value="8">' + ((shot === "8") ? "Iron to " : "") + ' Bunker</option>\
            </optgroup>\
            <optgroup label="Chip">\
                <option ' + ((shot === "9") ? "selected" : "") + ' value="9">' + ((shot === "9") ? "Chip to " : "") + ' Fairway</option>\
                <option ' + ((shot === "/") ? "selected" : "") + ' value="/">' + ((shot === "/") ? "Chip to " : "") + ' Rough</option>\
                <option ' + ((shot === "*") ? "selected" : "") + ' value="*">' + ((shot === "*") ? "Chip to " : "") + ' Green</option>\
                <option ' + ((shot === "-") ? "selected" : "") + ' value="-">' + ((shot === "-") ? "Chip to " : "") + ' Bunker</option>\
            </optgroup>\
            <option ' + ((shot === "0") ? "selected" : "") + ' value="0">Penalty</option>\
            <option ' + ((shot === "+") ? "selected" : "") + ' value="+">Putt</option>\
            </select></div></li>');
    }

});

var updateInfo = function(round, shots) {
    var embellish = "";
    var roundId = round[0].Id;
    var h = shots.find('select').attr("data-hole");

    //Build a string of the shot values
    shots.find('select :selected').each(function () {
        var val = "";
        val = $(this).attr('value');

        embellish = embellish + val;
    });

    //Remove the hole from the updates
    updatedHoles = updatedHoles.filter(function (el) {
        return el.RoundId === roundId && el.HoleNo !== h;
    });
    //Add the hole to the updatedHoles
    updatedHoles.push({ RoundId: roundId, HoleNo: h, Putts: 0, Embellish: embellish });

    //Clear and add the timeout again
    clearTimeout(updateHoles);

    var saveIn = 5000;
    //adjust the save time if we are on hole 18
    if (h === 18) saveIn = 1000;

    updateHoles = setTimeout(function () { submitEmbelish('UpdateHoles'); }, saveIn);
    round[0].RoundHoleDetailSummaries[h - 1].E = embellish;

    //update the putts 
    var _needle = "+"
        .replace(/\[/g, '\\[')
        .replace(/\]/g, '\\]');
    var putts = (embellish.match(new RegExp('[' + _needle + ']', 'g')) || []).length;

    var quickPutts = shots.closest(".collapse").find("[data-putts-hole='" + h + "']");

    quickPutts.val(putts);

    sumPutts(quickPutts.parent().parent().parent());

    //remove the updated round
    allData = allData.filter(function (el) {
        return el.Id !== round[0].Id;
    });

    //reAdd the round
    allData.push(round[0]);
}

window.onbeforeunload = function () {

    if (updatedHoles.length > 0){
    return "We are still saving your changes are you sure you want navigate away?";}
}

////Add the drop down to any selects
//$('body').on("focus touchstart", "select.shot", function () {
//    var self = $(this);
//    self.empty();
//    self.append($('<option disabled selected value=" "> Please Select </option>\
//<optgroup label="Wood">\
//    <option value="1">Fairway</option>\
//    <option value="2">Rough</option>\
//    <option value="3">Green</option>\
//    <option value="4">Bunker</option>\
//</optgroup>\
//<optgroup label="Iron">\
//    <option value="5">Fairway</option>\
//    <option value="6">Rough</option>\
//    <option value="7">Green</option>\
//    <option value="8">Bunker</option>\
//</optgroup>\
//<optgroup label="Chip">\
//    <option value="9">Fairway</option>\
//    <option value="/">Rough</option>\
//    <option value="*">Green</option>\
//    <option value="-">Bunker</option>\
//</optgroup>\
//<option value="0">Penalty</option>\
//<option value="+">Putt</option>\
//'));
//});

var getShotInfo = function (shot) {
    var desc;
    switch (shot) {
        case "1":
            desc = "Wood to Fairway";
            break;
        case "2":
            desc = "Wood to Rough";
            break;
        case "3":
            desc = "Wood to Green";
            break;
        case "4":
            desc = "Wood to Bunker";
            break;
        case "5":
            desc = "Iron to Fairway";
            break;
        case "6":
            desc = "Iron to Rough";
            break;
        case "7":
            desc = "Iron to Green";
            break;
        case "8":
            desc = "Iron to Bunker";
            break;
        case "9":
            desc = "Chip to Fairway";
            break;
        case "/":
            desc = "Chip to Rough";
            break;
        case "*":
            desc = "Chip to Green";
            break;
        case "-":
            desc = "Chip to Bunker";
            break;
        case "0":
            desc = "Penalty";
            break;
        case "+":
            desc = "Putt";
            break;
        default:
            desc = "Please Select";
    }
    return desc;
}