$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function ajax_success(data)
{
	$('#predictions').html(data);
	$('#predictions ul').listview();
	$('#predictions ul').listview('refresh');
	$("div[data-role='collapsible']").collapsible();
}

function update_predictions(type, param)
{
	if (type == "here") {
		$.ajax({
			type: "POST",
			data: {lat: param.coords.latitude.toFixed(6), lon: param.coords.longitude.toFixed(6)},
			url: '/next/api/location/',
			success: ajax_success,
			error: ajax_error,
			cache: false
		});
	}
	else if (type == "stop_id") {
		$.ajax({
			type: "GET",
			url: '/next/api/stop_id/'+param,
			success: ajax_success,
			error: ajax_error,
			cache: false
		});
	}
}

function ajax_error(jqXHR, textStatus, errorThrown) {
	$('#predictions').html("An unexpected error occured. ("+errorThrown+")");
}

function geo_success_callback(p)
{
	update_predictions("here", p);
}

function error_callback(p)
{
	alert('error='+p.code);
}

function get_stops_near_user() {
	//determine if the handset has client side geo location capabilities
	if(geo_position_js.init()){
		// Get the GPS position
		geo_position_js.getCurrentPosition(geo_success_callback,error_callback, enableHighAccuracy=true, maximumAge=1000);
	}
	else{
	   alert("Functionality not available");
	}
}

function show_spinning_wheel(message) {
	message = message || "Loading predictions for stops near you…";
	$('#predictions').html('<p><img src="/static/img/loading.gif" />' + message + ' </p>');
}

$(document).ready(function () {
	if (($('#for_stop_id').length == 0)) {
		get_stops_near_user();
	}
});

$('#by_stop_id').submit(function() {
	update_predictions("stop_id", $("input#stopid").val());
	// Will prevent the default behavior
	return false;
});

$('#stops_near_me').submit(function() {
	show_spinning_wheel();
	get_stops_near_user();
	// Will prevent the default behavior
	return false;
});
