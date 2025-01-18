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

def read_gdb_output(gdb_process):
    """
    Reads the GDB output and captures the current line after a 'next' command
    """
    output = ""
    pattern = r'^\s*\d+\s+(int|float|char|double|long|short)\s+\w+\s*=\s*[^;]+;|' \
              r'^\s*\d+\s+\w+\s*=\s*.+;|' \
              r'^\s*\d+\s+.*;$'  # Matches variable declarations, assignments, or valid C statements

    try:
        is_windows = platform.system() == "Windows"
        start_time = time.time()
        timeout = 10

        while True:
            if is_windows:
                line = gdb_process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                # print(f"Debug - Raw line: {line}")  # Debug print

                # Process the line to remove the `(gdb)` prompt
                if line.startswith("(gdb)"):
                    line = line.replace("(gdb)", "").strip()

                # Check each line against the pattern
                for subline in line.split("(gdb)"):
                    subline = subline.strip()
                    if not subline:
                        continue

                    match = re.search(pattern, subline)
                    if match:
                        matched_line = match.group(0)
                        # print(f"Debug - Processing line: {subline}")
                        # print(f"Debug - Matched line: {matched_line}")
                        return matched_line

            if time.time() - start_time > timeout:
                print("Timeout waiting for GDB response")
                break

            # time.sleep(0.1)

    except Exception as e:
        print(f"Error reading GDB output: {e}")
        print(f"Current output buffer: {output}")  # Debug print
    
    return None


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
