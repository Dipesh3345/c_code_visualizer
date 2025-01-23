import re
import platform
import time
address_base = 0x1000  # Starting address for memory allocation (mocked for demonstration)
variable_address_map = {}
def parse_gdb_output(output):
    memory_data = []
    global address_base
    global variable_address_map
    type_size = {
        "int": 4,
        "float": 4,
        "char": 1
    }

    for line in output.splitlines():
        # Match scalar variable declarations, e.g., "5       int x = 10;"
        scalar_match = re.match(
            r'^\s*\d+\s+(int|float|char)\s+([\w]+)\s*=\s*(.+);$', 
            line
        )
        if scalar_match:
            var_type = scalar_match.group(1).strip()
            variable = scalar_match.group(2).strip()
            value = scalar_match.group(3).strip()
            variable_address_map[variable] = f"0x{address_base:06x}"
            memory_data.append({
                "variable": variable,
                "value": value,
                "type": var_type,
                "address": f"0x{address_base:06x}"
            })
            # Increment base address by the size of the type
            address_base += type_size.get(var_type, 4)

        # Match array declarations, e.g., "6       int arr[] = {1, 2, 3, 4};"
        array_match = re.match(
            r'^\s*\d+\s+(int|float|char)\s+([\w]+)\s*\[\d*\]\s*=\s*\{\s*([^}]*)\s*\};$', 
            line
        )
        if array_match:
            print("Hello")
            array_type = array_match.group(1).strip()
            array_name = array_match.group(2).strip()
            # Extract values if provided; otherwise, initialize with default values
            values_str = array_match.group(3).strip()
            variable_address_map[array_name] = f"0x{address_base:06x}"
            if values_str:  # Non-empty initializer list
                values = [v.strip() for v in values_str.split(",")]
            else:  # Empty initializer list, default values based on type
                array_size_match = re.search(r'\[(\d+)\]', line)
                if array_size_match:
                    array_size = int(array_size_match.group(1))
                    default_value = {
                        "int": "0",
                        "float": "0.0",
                        "char": "'\\0'"
                    }.get(array_type, "0")  # Default to "0" if type is unknown
                    values = [default_value] * array_size
                else:
                    values = []  # Handle edge case if no size is specified

            # Generate continuous memory addresses for array elements
            addresses = []
            for _ in values:
                addresses.append(f"0x{address_base:06x}")
                address_base += type_size.get(array_type, 4)

            memory_data.append({
                "variable": array_name,
                "value": values,
                "type": f"{array_type}[]",
                "address": addresses
            })
        pointer_match = re.match(
            r'^\s*\d+\s+(int|float|char|double|long|short)\s*\*\s*([\w]+)\s*=\s*([^;]+);$', 
            line
        )
        if pointer_match:
            var_type = pointer_match.group(1).strip()  # Data type (e.g., int, float, char)
            pointer_name = pointer_match.group(2).strip()  # Pointer variable name (e.g., ptr)
            value = pointer_match.group(3).strip()  # Assigned value (e.g., NULL, &var)
            # Resolve address if the pointer is assigned a variable address (e.g., &a)
            if value.startswith("&"):
                referenced_variable = value[1:]  # Remove the '&' to get the variable name
                resolved_address = variable_address_map.get(referenced_variable, "NULL")
            else:
                resolved_address = value  # For cases like NULL

            memory_data.append({
            "variable": pointer_name,
            "value": resolved_address,  # Store the assigned value (e.g., NULL or address)
            "type": f"{var_type}*",  # Indicate it's a pointer type
            "address": f"0x{address_base:06x}"  # Assign a unique address
            })

            # Increment base address by the size of the pointer (typically 8 bytes for 64-bit systems)
            address_base += 8
    print(memory_data)
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
    statement_pattern = r'^\s*\d+\s+(int|float|char|double|long|short)\s+\w+\[.*\]\s*=\s*{.*};|' \
                    r'^\s*\d+\s+(int|float|char|double|long|short)\s+\w+\[.*\];|' \
                    r'^\s*\d+\s+(int|float|char|double|long|short)\s+\w+\s*=\s*[^;]+;|' \
                    r'^\s*\d+\s+\w+\s*=\s*.+;|' \
                    r'^\s*\d+\s+(int|float|char|double|long|short)\s*\*\s*\w+\s*=\s*[^;]+;|' \
                    r'^\s*\d+\s+(int|float|char|double|long|short)\s*\*\s*\w+\s*;|' \
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
            print(f"Raw line: {line}")
            # Check if the line matches a variable/statement
            if not matched_line:
                statement_match = re.search(statement_pattern, line)
                if statement_match:
                    matched_line = statement_match.group(0)
                    if count == 0:
                        line = gdb_process.stdout.readline()
                        line = gdb_process.stdout.readline()
            
            print(f"Matched Line: {matched_line}")
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
    Simulates memory management by extracting variables, arrays, and their values from C code.
    
    Args:
        c_code (str): The C code to extract memory data from.
    
    Returns:
        list: A list of dictionaries containing variable information with fields:
            - "variable": Name of the variable.
            - "value": The assigned value(s).
            - "type": The type of the variable (int, float, char, etc.).
            - "address": Simulated memory address.
    """
    memory_data = []

    # Regular expressions for simple variables and arrays
    simple_var_pattern = r'\b(int|float|char)\s+(\w+)\s*=\s*([^;]+);'
    array_pattern = r'\b(int|float|char)\s+(\w+)\s*\[.*\]\s*=\s*\{([^}]+)\};'

    # Extract simple variables
    for match in re.finditer(simple_var_pattern, c_code):
        var_type, var_name, var_value = match.groups()
        memory_address = f"0x{hash(var_name) & 0xFFFFFF:06x}"

        memory_data.append({
            "variable": var_name,
            "value": var_value.strip(),
            "type": var_type,
            "address": memory_address,
        })

    # Extract arrays
    for match in re.finditer(array_pattern, c_code):
        var_type, var_name, array_values = match.groups()
        values = [value.strip() for value in array_values.split(",")]

        # Simulate continuous memory allocation for array elements
        base_address = hash(var_name) & 0xFFFFFF
        addresses = [f"0x{(base_address + i * 4) & 0xFFFFFF:06x}" for i in range(len(values))]

        memory_data.append({
            "variable": var_name,
            "value": values,
            "type": f"{var_type}[]",
            "address": addresses,
        })
    print(f"memory_data:{memory_data}")
    return memory_data
