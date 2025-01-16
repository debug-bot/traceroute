from django.shortcuts import render
from .models import Probe


# Create your views here.
def main(request):
    probes = Probe.objects.all()
    return render(request, "main.html", {"probes": probes})


import subprocess
import platform
from django.http import JsonResponse


def traceroute_view(request):
    # Get the domain from the GET parameter
    domain = request.GET.get("domain")

    if not domain:
        return JsonResponse({"error": "Domain parameter is required"}, status=400)

    try:
        # Determine the operating system
        system = platform.system()
        if system == "Windows":
            # Use tracert for Windows
            command = ["tracert", domain]
        else:
            # Use traceroute for Unix-based systems
            command = ["traceroute", domain]

        # Run the traceroute command
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return JsonResponse(
                {"error": f"Traceroute failed: {stderr.decode('utf-8')}"}, status=500
            )

        # Parse the traceroute output
        output_lines = stdout.decode("utf-8").split("\n")
        parsed_output = [line.strip() for line in output_lines if line.strip()]

        return JsonResponse({"domain": domain, "traceroute": parsed_output})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
