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