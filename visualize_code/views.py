from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
import subprocess
import json
import re

def home(request):
    context = {}
    
    if request.method == 'POST':
        # Get the action type: 'run_code' or 'visualize_memory'
        action = request.POST.get('action', '')
        # Get the submitted C code
        c_code = request.POST.get('c_code', '')
        context['c_code'] = c_code  # Pass the entered code back to the template
        print(action)
        if not c_code.strip():
            context['error'] = "No C code provided."
            return render(request, 'visualize_code/home.html', context)

        # Save C code to a temporary file
        with open('temp.c', 'w') as file:
            file.write(c_code)

        try:
            if action == 'run_code':
                print("Hello")
                # Compile and run the C code
                result = subprocess.run(['gcc', '-mconsole', 'temp.c', '-o', 'temp.out'], capture_output=True, text=True)
                if result.returncode != 0:
                    # Compilation error
                    context['error'] = result.stderr
                else:
                    # Run the compiled program
                    output = subprocess.run(['./temp.out'], capture_output=True, text=True)
                    context['output'] = output.stdout

            elif action == 'visualize_memory':
                # Extract variable information for memory management visualization
                memory_data = extract_memory_data(c_code)
                context['memory_data'] = mark_safe(json.dumps(memory_data))  # Pass as JSON-safe

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'visualize_code/home.html', context)

def extract_memory_data(c_code):
    """
    Simulates memory management by extracting variables and their values from C code.
    """
    memory_data = []
    # Regular expression to match simple variable declarations (int, float, char)
    var_pattern = r'\b(int|float|char)\s+(\w+)\s*=\s*([^;]+);'

    for match in re.finditer(var_pattern, c_code):
        var_type, var_name, var_value = match.groups()
        # Generate a mock memory address (hexadecimal, for visualization)
        memory_address = f"0x{hash(var_name) & 0xFFFFFF:06x}"

        memory_data.append({
            "variable": var_name,
            "value": var_value.strip(),
            "type": var_type,
            "address": memory_address,
        })

    return memory_data
