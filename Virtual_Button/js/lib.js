$(document).ready(function(){
	var requestBtn = document.getElementById("requestBtn");
	var timerLbl = document.getElementById("timer");
	var timeDisabled = 5400000; //in milliseconds
			
	// Disable button if break request is not ready
	if(localStorage.getItem("storedTimestamp") !== null){
		var storedTimestamp = localStorage.getItem("storedTimestamp"); // in milliseconds
		var currentTimestamp = Date.now(); // in milliseconds
		var delta = currentTimestamp - storedTimestamp; // in milliseconds

		if(delta < timeDisabled){
			// Disable button
			$(requestBtn).attr("disabled", true);
			
			// Add timer
			startTimer(localStorage.getItem("timer"), timerLbl);
		} else {
			// Enable button
			$(requestBtn).attr("disabled", false);
		}
	}
		
	// Define actions that are performed when the button is clicked
	$("#requestBtn").click(function(){
		// Send break request as JSON to Home Assistant
		$.ajax({
			type: "POST",
			url: "http://192.168.1.135:8123/api/services/input_boolean/toggle",
			data: "{\"entity_id\": \"input_boolean.breakrequest\"}"
		});				
					
		// Add a timestamp to localStorage indicating the moment when the button was clicked
		localStorage.setItem("storedTimestamp", Date.now());
		
		// Disable button for the specified amount of time
		$(requestBtn).attr("disabled", true);
		setTimeout(function() { enableSubmit(requestBtn) }, timeDisabled);
		
		// Display the amount of time until new break request can be sent
		startTimer(timeDisabled / 1000, timerLbl);
	});
});
		

var enableSubmit = function(parameter) {
	// Enable the button 
	$(parameter).removeAttr("disabled");
			
	// Remove the timestamp from localStorage
	localStorage.removeItem("storedTimestamp");	
}

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    myTimer = setInterval(function () {
		// Parse values
        minutes = parseInt(timer / 60, 10)
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
		
		// Display timer
        display.textContent = "Next request in: " + minutes + ":" + seconds + " min.";
		localStorage.setItem("timer", timer);

        if (--timer < 0) {
			// Remove timer
			clearInterval(myTimer);
			display.textContent = "";
			localStorage.removeItem("timer");

			// Refresh page
			location.reload();
		}
    }, 1000);
}
