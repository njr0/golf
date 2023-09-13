// Allow json data to be displayed as string, useful for debugging
// (if somehow you are unable to use console)
Handlebars.registerHelper('toJSON', function(object){
    return new Handlebars.SafeString(JSON.stringify(object));
});


// Allow logical operators to be used in IF/ELSE statements.
// Usage: {{#ifCond var1 '==' var2}}, the quote is required on the operator.
Handlebars.registerHelper("ifCond", function (v1, operator, v2, options) {
    switch (operator) {
        case '==':
            return (v1 == v2) ? options.fn(this) : options.inverse(this);
        case '===':
            return (v1 === v2) ? options.fn(this) : options.inverse(this);
        case '<':
            return (v1 < v2) ? options.fn(this) : options.inverse(this);
        case '<=':
            return (v1 <= v2) ? options.fn(this) : options.inverse(this);
        case '>':
            return (v1 > v2) ? options.fn(this) : options.inverse(this);
        case '>=':
            return (v1 >= v2) ? options.fn(this) : options.inverse(this);
        case '&&':
            return (v1 && v2) ? options.fn(this) : options.inverse(this);
        case '||':
            return (v1 || v2) ? options.fn(this) : options.inverse(this);
        default:
            return options.inverse(this);
    }
});


// Each helper with an upperlimit for large result set. Usage:
/*
    {{#eachUpto this 5}}
        ...
    {{/eachUpto}}
*/
Handlebars.registerHelper('eachUpto', function (ary, max, options) {
    if (!ary || ary.length === 0)
        return options.inverse(this);

    var result = [];
    for (var i = 0; i < max && i < ary.length; ++i)
        result.push(options.fn(ary[i]));
    return result.join("");
});


// HH: Temp. solution to calculate which css class to use for the chat message:
Handlebars.registerHelper("getMessageType", function (userPlayer, userSection, messagePlayer, messageSection) {
   
    if (userPlayer == messagePlayer && userSection == messageSection) {
        return new Handlebars.SafeString("t-msg");
    } else {
        return new Handlebars.SafeString("m-msg");
    }
});

// Template to calculate nth text
Handlebars.registerHelper("place", function(num) {

    var orderStr = num.toString();
    if (orderStr.endsWith("11") || orderStr.endsWith("12") || orderStr.endsWith("13")) return orderStr + "th";
    if (orderStr.endsWith("1")) return orderStr + "st";
    if (orderStr.endsWith("2")) return orderStr + "nd";
    if (orderStr.endsWith("3")) return orderStr + "rd";
    return orderStr + "th";
});

// Template to calculate nth text
Handlebars.registerHelper("occurrences", function (haystack, needle) {
    haystack += "";
    var _needle = needle
        .replace(/\[/g, '\\[')
        .replace(/\]/g, '\\]');
    return (
        haystack.match(new RegExp('[' + _needle + ']', 'g')) || []
    ).length;
});

// Template to calculate hole stats
Handlebars.registerHelper("holeStat", function (holeDetails, hole, search) {

    if (search == "P" || search=="SI")
    {
        return holeDetails[hole][search];
    } else {
   
    //hole 0 based
    var details = holeDetails[hole].E;
    details += "";
    var _search = search
        .replace(/\[/g, '\\[')
        .replace(/\]/g, '\\]');

    var result =  details.match(new RegExp('[' + _search + ']', 'g')) || [].length;

    if (!result == 0) {
        result = result.length;
    }

    return result;
 }
});


// substr(length, context):
Handlebars.registerHelper('substr', function (length, context) {
    if (typeof truncate === 'undefined') {
        truncate = false;
    }
    if (context.length > length) {
        return context.substring(0, length);
    } else {
        return context;
    }
});

// hideComments:
Handlebars.registerHelper("hiddenComments", function (count) {
    if (count > 5) {
        var grandTotal = count - 5;
        var result = '<a class="show-all view" href="#"><i class="fa fa-eye"></i> View ' + grandTotal + ' more</a>' +
            '<a class="hide-all view" href="#">Hide ' + grandTotal + ' comments </a>';
        return new Handlebars.SafeString(result);
    } else {
        return new Handlebars.SafeString("");
    }
});



// Alias:
Handlebars.registerHelper("getInitials", function(username) {
    var vals = username.split(" ");
    var fn = vals[0].substring(0, 1);
    var sn = "";
    if (vals[1] !== undefined || vals[1] !== "") {
        sn = vals[1].substring(0, 1);
    }
    
    return fn + sn;
});

//get an Item from an array
Handlebars.registerHelper('arrayItem', function (item, idx) {

    return item[idx];
});

Handlebars.registerHelper('times', function (n, block) {
    var accum = '';
    for (var i = 0; i < n; ++i)
        accum += block.fn(i);
    return accum;
});

Handlebars.registerHelper('ProfilePic', function(source) {

    if (source.length < 1) {
        return new Handlebars.SafeString("<div class=\"picture-lg square\"> <i class=\"fa fa-user\"></i></div>");

    } else {
        if (source.includes("picsrv")) {
            return new Handlebars.SafeString("<div class=\"picture-lg\" style=\"background-image:url('" + source + "')\"></div>");
        } else {
            return new Handlebars.SafeString("<div class=\"picture-lg square\" style=\"background-image:url('" + source + "')\" ></div>");
        }

    }
});

// This can be seen as a parent-level helper.
// You call this on pages where you want to use all the custom handlebar helpers,
// and pass along any params/vars you need.
// We should look to slowly move the above registers into this function.
function initHandlebarHelpers(opts) {

    function validate() {
        if (typeof (opts.userId) == "undefined" || typeof(opts.userId) !== "number") {
            throw "opts.UserId must be populated.";
        }
    }

    // currentUserId = the current logged in user.
    // userId == the user posted the comment.
    // We cannot pull the user id object from handlebar template so it's done
    // as an injected value from a function. If you can improve this be my guest.
    function initCommentRemove(currentUserId) {
        Handlebars.registerHelper("showRemoveComment", function (userId, commentId) {
            if (currentUserId == userId) {
                var result =
                    "<a href='#/' class='comment-remove' data-comment-id=" + commentId + ">" +
                        "<i class='fa fa-trash-o'></i></a>";
                return new Handlebars.SafeString(result);
            } else {
                return new Handlebars.SafeString("");
            }
        });
    }

    validate();
    initCommentRemove(opts.userId);
}