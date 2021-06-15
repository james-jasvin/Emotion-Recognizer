function reloadPage() {
	location.reload();
	$("#error").hide();
}

function showLoading() {
	$("#dropzone").hide();
	$("#error").hide();
	$("#loading").show();
}

$(document).ready(function() {

	// These scripts are associated with only home page, so that is why we added class "homePage" to body tag 
	// of home.html and then check it here in order to ensure which page this is
	if ($("body").hasClass("homePage")) {

		// If user is on home page but URL bar shows "jobs" or anything else
		// because of unauthorized access by user to "jobs" endpoint without submitting form
		// then redirect user to home with Unauthorized access error code (102)
		var location = window.location.href.split('/');
		var currentLocation = location[location.length - 1];
		if (currentLocation == "jobs")
			window.location.replace("../102");


		// The error message has an "x" button that represents close
		// This Slide Up animation will be triggered whenever that close button is clicked
		$(".close-button").click(function() {
			$(".close-button").parent().slideUp(1000);
		});	

		/*
			* Onclick event handler on the "Display Results" button which does the following actions,
			* 1. Hide the error message div element
			* 2. Show the loading screen
			* 3. Submit a POST request to the "jobs" route using an AJAX request which will start the Redis job
			* 4. Once AJAX request is successfully completed, the polling function is called which will ask for submitted job status
			* 5. If AJAX request fails, then Client is redirected to home page with the appropriate error message
		*/

		var resultsButton = document.getElementById("results");
		resultsButton.onclick = function(event) {
			
			// Hide the error message and show loading spinners on submission
			showLoading();

			// Send AJAX POST request to jobs route, processData and contentType are required for file uploads with 
			// AJAX requests, otherwise it fails
			$.ajax({
				url: '/jobs',
				data: "Start Redis job",
				method: 'POST',
				processData: false,
				contentType: false
			})
			.done((res) => {
				// If response has status as fail then it means server-side validation failed, so redirect
				// to home page with given error_code
				if (res['status'] === "fail") {
					var error_code = res['error_code'];
					window.location.replace('../home/' + error_code);
				}
				else {
					console.log("Calling Poller");
					getJobStatus(res['job_id']);
				}
			})
			.fail((err) => {
				console.log("Failed form submission");
				console.log(err);
			});
		}
	}
}

/**
	* Poller function that asks for job status of given job every 2 seconds via an AJAX GET request to "jobs/job_id" route
	* If job has finished execution, i.e., jobStatus = finished, then, send client to results page
	* where output files will be fetched from the session dictionary and accordingly output will be displayed
	* @param {String} jobId: Job ID of job to keep track of
	* @return {Boolean} : Returns false as a placeholder value to prevent polling when job is completed or failed
*/
function getJobStatus(jobID) {
	$.ajax({
		url: `/jobs/${jobID}`,
		method: 'GET'
	})
	.done((res) => {
		var jobStatus = res['data']['job_status'];

		if (jobStatus === 'finished') {
			window.location.href = '../results/';
			return false;
		}
		else if (jobStatus === 'failed') {
			return false;
		}

		// This means that job has neither failed nor finished, so continue polling
		// Call poller function every 2 seconds (2000 ms)
		setTimeout(function() {
		  getJobStatus(res['data']['job_id']);
		}, 2000);
	})
	.fail((err) => {
		console.log(err);
	});
}