import json
from django.http import JsonResponse, HttpResponseBadRequest
from .helpers import run_code, submit_code
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def run_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
        output = run_code(
            data["language"],
            data["code"],
            data.get("input_data", ""),
            data.get("time_limit", 5),
            data.get("memory_limit", 128)
        )
        return JsonResponse({"output": output})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def submit_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
        result = submit_code(
            data["language"],
            data["code"],
            data["testcases"],
            data.get("time_limit", 5),
            data.get("memory_limit",128)
        )
        return JsonResponse(result) 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



