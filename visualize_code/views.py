from .helpers.gdb_helper import start_debugging_session, step_forward_session, stop_debugging_session
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
import subprocess
import json
import os

def home(request):
    """
    Renders the main page for the C code visualization tool.
    Handles C code submission and compilation.
    """
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
            # Save the submitted C code to a temporary file
            with open(temp_file, 'w') as file:
                file.write(c_code)

            # Action: Run the code
            if action == 'run_code':
                compile_result = subprocess.run(
                    ['gcc', '-g', temp_file, '-o', 'tempfile.out'],
                    capture_output=True, text=True
                )
                if compile_result.returncode != 0:
                    context['error'] = compile_result.stderr
                else:
                    execution_result = subprocess.run(['./tempfile.out'], capture_output=True, text=True)
                    context['output'] = execution_result.stdout

            # Action: Visualize memory
            elif action == 'visualize_memory':
                from .helpers.memory_helper import extract_memory_data
                memory_data = extract_memory_data(c_code)
                context['memory_data'] = mark_safe(json.dumps(memory_data))

        except Exception as e:
            context['error'] = str(e)

        finally:
            # Cleanup temporary files
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists('tempfile.out'):
                os.remove('tempfile.out')

    return render(request, 'visualize_code/home.html', context)

@csrf_exempt
def start_debugging(request):
    """
    Starts a debugging session using GDB.
    """
    if request.method == "POST":
        try:
            response = start_debugging_session(request)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)

@csrf_exempt
def stop_debugging(request):
    """
    Stops an active debugging session.
    """
    if request.method == "POST":
        try:
            response = stop_debugging_session(request)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)

@csrf_exempt
def step_forward(request):
    """
    Steps forward in the debugging session using GDB.
    """
    if request.method == "POST":
        try:
            response = step_forward_session(request)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)
