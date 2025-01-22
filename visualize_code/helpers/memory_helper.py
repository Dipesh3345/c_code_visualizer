import re
import platform
import time

def parse_gdb_output(output):
    memory_data = []

    for line in output.splitlines():
        # Match variable declarations with line numbers, e.g., "5       char c = 'X';"
        match = re.match(r'^\s*\d+\s+(?:int|float|char|double|long|short|unsigned)?\s*([\w]+)\s*=\s*(.+);$', line)
        if match:
            variable = match.group(1).strip()  # Extract the variable name
            value = match.group(2).strip()    # Extract the value
            memory_data.append({
                "variable": variable,
                "value": value,
                "address": f"0x{hash(variable) & 0xFFFFFF:06x}"
            })

    return memory_data


def extract_current_line(gdb_output):
    """
    Extracts the current line being executed from GDB output.
    """
    current_line = None

    # Adjusted regex to match a line number at the start of the string
    line_match = re.search(r'^\s*(\d+)\s+', gdb_output)
    if line_match:
        current_line = int(line_match.group(1))  # Extract the line number

    return current_line


def read_gdb_output(gdb_process, count):
    """
    Reads the GDB output and captures the current line and the current function name.
    
    Args:
        gdb_process: The subprocess.Popen object for the running GDB process.
    
    Returns:
        A dictionary containing:
            - "matched_line": The matched line (variable declaration, assignment, or valid C statement).
            - "function_name": The current function name (if extracted).
    """
    # Patterns for matching
    statement_pattern = r'^\s*\d+\s+(int|float|char|double|long|short)\s+\w+\s*=\s*[^;]+;|' \
                        r'^\s*\d+\s+\w+\s*=\s*.+;|' \
                        r'^\s*\d+\s+.*;$'
    function_name_pattern = r'(?<=in\s)(\w+)\s*(?=\()'

    timeout = 10  # Timeout in seconds
    start_time = time.time()
    output = ""
    matched_line = None
    function_name = None
    i = 0
    print(count)
    try:
        is_windows = platform.system() == "Windows"

        while True:
            # Read a line from GDB's output
            if is_windows:
                line = gdb_process.stdout.readline()
            else:
                line = gdb_process.stdout.read(1).decode("utf-8")
            
            if not line:
                # Exit the loop if no output is received within the timeout
                if time.time() - start_time > timeout:
                    print("Timeout waiting for GDB response.")
                    break
                continue

            line = line.strip()
            output += line + "\n"  # Accumulate output for debugging if needed

            # Remove the `(gdb)` prompt
            line = line.replace("(gdb)", "").strip()

            # Check if the line matches a variable/statement
            if not matched_line:
                statement_match = re.search(statement_pattern, line)
                if statement_match:
                    matched_line = statement_match.group(0)
                    if count == 0:
                        line = gdb_process.stdout.readline()
                        line = gdb_process.stdout.readline()

            # Check if the line contains the function name (from `info frame`)
            if not function_name:
                function_match = re.search(function_name_pattern, line)
                if function_match:
                    function_name = function_match.group(0)

            # Return once both matched_line and function_name are found
            if matched_line or function_name:
                return {"matched_line": matched_line, "function_name": function_name}

            # Break if timeout occurs
            if time.time() - start_time > timeout:
                print("Timeout waiting for GDB response.")
                break

    except Exception as e:
        print(f"Error reading GDB output: {e}")
        print(f"Partial Output: {output}")  # Debugging information

    # Return results, even if partially found
    return {"matched_line": matched_line, "function_name": function_name}


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
