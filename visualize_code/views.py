from .helpers.gdb_helper import start_debugging_session, step_forward_session, stop_debugging_session
from .helpers.memory_helper import extract_memory_data
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
import subprocess
import json
import os

gdb_sessions = {}
gdb_process = None
current_line = 0

def home(request):
    context = {}
    if request.method == 'POST':
        action = request.POST.get('action', '')
        c_code = request.POST.get('c_code', '')
        context['c_code'] = c_code

        if not c_code.strip():
            context['error'] = "No C code provided."
            return render(request, 'visualize_code/home.html', context)

        temp_file = 'tempfile.c'
        try:
            with open(temp_file, 'w') as file:
                file.write(c_code)

            if action == 'run_code':
                compile_result = subprocess.run(['gcc', '-g', temp_file, '-o', 'tempfile.out'], capture_output=True, text=True)
                if compile_result.returncode != 0:
                    context['error'] = compile_result.stderr
                else:
                    execution_result = subprocess.run(['./tempfile.out'], capture_output=True, text=True)
                    context['output'] = execution_result.stdout

            elif action == 'visualize_memory':
                memory_data = extract_memory_data(c_code)
                context['memory_data'] = mark_safe(json.dumps(memory_data))

        except Exception as e:
            context['error'] = str(e)
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists('tempfile.out'):
            os.remove('tempfile.out')

    return render(request, 'visualize_code/home.html', context)


@csrf_exempt
def start_debugging(request):
    try:
        if request.method == "POST":
            # Directly return the response from start_debugging_session
            return JsonResponse(start_debugging_session(request))
        else:
            return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def stop_debugging(request):
    try:
        if request.method == "POST":
            # Directly return the response from stop_debugging_session
            return JsonResponse(stop_debugging_session(request))
        else:
            return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def step_forward(request):
    try:
        if request.method == "POST":
            # Directly return the response from step_forward_session
            return JsonResponse(step_forward_session(request))
        else:
            return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
