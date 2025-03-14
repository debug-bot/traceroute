// Show spinner + overlay before page unload
window.addEventListener("beforeunload", function () {
	document.getElementById("container-overlay").style.display = "block";
	document.getElementById("spinner-center").style.display = "block";
});

// Hide them once page + JS fully loaded
window.addEventListener("load", function () {
	document.getElementById("container-overlay").style.display = "none";
	document.getElementById("spinner-center").style.display = "none";
});

function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== "") {
		const cookies = document.cookie.split(";");
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) === name + "=") {
				cookieValue = decodeURIComponent(
					cookie.substring(name.length + 1)
				);
				break;
			}
		}
	}
	return cookieValue;
}

const csrftoken = getCookie("csrftoken");

$.ajaxSetup({
	beforeSend: function (xhr, settings) {
		if (
			!/^GET|HEAD|OPTIONS|TRACE$/i.test(settings.type) &&
			!this.crossDomain
		) {
			xhr.setRequestHeader("X-CSRFToken", csrftoken);
		}
	},
});

function handleAllOptionChange(event) {
	const select = event.target;
	const allOption = select.querySelector('option[value="all"]');
	// Gather all selected values
	const selectedValues = Array.from(select.selectedOptions).map(
		(o) => o.value
	);
	// Case 1: "All" + another option => keep only "All"
	if (selectedValues.includes("all") && selectedValues.length > 1) {
		for (let opt of select.options) {
			opt.selected = opt.value === "all";
		}
		// trigger change select
		select.dispatchEvent(new Event("change"));
	}
	// Case 2: multiple selected, but not "All" => unselect "All"
	else if (selectedValues.length > 1 && !selectedValues.includes("all")) {
		allOption.selected = false;
		// trigger change select
		select.dispatchEvent(new Event("change"));
	}
}

function slowScrollToBottom(duration) {
	const startY = window.scrollY || document.documentElement.scrollTop;
	const endY = document.body.scrollHeight;
	const distance = endY - startY;
	let startTime = null;

	function animation(currentTime) {
		if (startTime === null) startTime = currentTime;
		const elapsed = currentTime - startTime;
		// Progress ranges from 0 to 1
		const progress = Math.min(elapsed / duration, 1);

		// Scroll to the current position
		window.scrollTo(0, startY + distance * progress);

		// Continue animating if we haven't reached 1
		if (progress < 1) {
			requestAnimationFrame(animation);
		}
	}

	requestAnimationFrame(animation);
}
