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