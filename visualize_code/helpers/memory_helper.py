from clang.cindex import Index, CursorKind, TypeKind
import re
import platform
import time
import wexpect
import queue

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
            #print(f"Raw line: {line}")
            # Check if the line matches a variable/statement
            if not matched_line:
                statement_match = re.search(statement_pattern, line)
                if statement_match:
                    matched_line = statement_match.group(0)
                    if count == 0:
                        line = gdb_process.stdout.readline()
                        line = gdb_process.stdout.readline()
            
            #print(f"Matched Line: {matched_line}")
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


def extract_local_variables(gdb_process):
    """
    Extracts local variables and their values from GDB output.

    Args:
        gdb_process: The subprocess.Popen object for the running GDB process.

    Returns:
        A list of dictionaries, each containing:
            - "name": The name of the local variable.
            - "value": The value of the local variable.
    """

    variable_pattern = r'^\s*(\w+)\s*=\s*(.*)'  # Simplified pattern for variable assignments
    local_variables = []

    try:
        is_windows = platform.system() == "Windows"

        while True:
            # Read a line from GDB's output
            if is_windows:
                line = gdb_process.stdout.readline()
            else:
                line = gdb_process.stdout.read(1).decode("utf-8")

            if not line:
                break

            line = line.strip()
            print(line)
            # Check if the line contains a variable assignment
            if line.startswith("Value of"):
                variable_match = re.search(variable_pattern, line)
                if variable_match:
                    variable_name = variable_match.group(1)
                    variable_value = variable_match.group(2)
                    local_variables.append({
                        "name": variable_name,
                        "value": variable_value
                    })

    except Exception as e:
        print(f"Error reading GDB output: {e}")

    return local_variables


def parse_with_clang(statement):
    code = f"void temp() {{ {statement} }}"
    index = Index.create()
    translation_unit = index.parse('example.c', args=['-std=c11'], unsaved_files=[('example.c', code)])
    type_size = {
        "int": 4,
        "float": 4,
        "char": 1,
        "double": 8,
        "long": 8,
        "short": 2
    }
    # List to store parsed memory data
    memory_data = []

    # Function to extract the raw code for a node
    def extract_code(node):
        # Ensure the start and end offsets are within bounds
        start = node.extent.start.offset
        end = node.extent.end.offset
        return code[start:end].strip()  # Trim any extra spaces or newlines


    # Recursive function to parse initializers
    def parse_initializer(node):
        if node.kind == CursorKind.INIT_LIST_EXPR:
            return [parse_initializer(child) for child in node.get_children()]
        elif node.kind in {CursorKind.INTEGER_LITERAL, CursorKind.FLOATING_LITERAL}:
            return float(extract_code(node)) if '.' in extract_code(node) else int(extract_code(node))
        else:
            return extract_code(node)

    def parse_initializer_list(node):
        values = []
        for child in node.get_children():
            # print(f"Child kind: {child.kind}, code: {extract_code(child)}")  # Debugging
            if child.kind == CursorKind.INTEGER_LITERAL:
                values.append(int(extract_code(child)))  # Convert to int
            elif child.kind == CursorKind.FLOATING_LITERAL:
                # print("Detected floating literal")
                try:
                    values.append(float(extract_code(child)))  # Convert to float
                except ValueError:
                    values.append(0.0)  # Handle parsing errors gracefully
            elif child.kind == CursorKind.CHARACTER_LITERAL:
                raw_value = extract_code(child).strip("'")  # Extract character literal
                if len(raw_value) == 1:
                    values.append(raw_value)  # Append the character
                else:
                    values.append(' ')  # Default to space for invalid characters
            elif child.kind == CursorKind.UNEXPOSED_EXPR:
                # print("Unexposed expression detected")
                # Dive into `UNEXPOSED_EXPR` to find the actual literal
                grandchild_values = parse_initializer_list(child)
                values.extend(grandchild_values)
        return values


        # Helper function to parse arrays
    def parse_array(node):
        global address_base
        element_type = node.type.element_type.spelling  # Determine the type of array elements
        element_size = type_size.get(element_type, 4)  # Get the size of the array elements
        array_size = node.type.element_count or 0  # Get the size if explicitly specified
        values = []
        addresses = []

        # Check if there is an initializer list
        initializer = None
        for child in node.get_children():
                if child.kind == CursorKind.INIT_LIST_EXPR:
                    initializer = parse_initializer_list(child)

        print(initializer)

        # If initializer is present, use it; otherwise, default to type-specific zeros
        if initializer:
            values = initializer
            array_size = len(initializer)  # Update size based on initializer
        else:
            # Default values for uninitialized arrays based on element type
            if element_type == "int":
                values = [0] * array_size
            elif element_type == "float":
                values = [0.0] * array_size
            elif element_type == "char":
                values = [' '] * array_size  # Default to null character

        # Generate addresses for each array element
        for _ in range(array_size):
            addresses.append(f"0x{address_base:06x}")
            address_base += element_size  # Increment address by size of type

        return values, addresses

    # Recursive function to visit all nodes
    def visit_node(node):
        global address_base
        if node.kind == CursorKind.VAR_DECL:  # Check if it's a variable declaration
            var_name = node.spelling
            var_type = node.type.spelling
            var_value = None
            addresses = []

            if node.type.kind == TypeKind.CONSTANTARRAY:
                var_value, addresses = parse_array(node)
                var_type = f"{node.type.element_type.spelling}[]"

            else:  # Handle non-array variables
                for child in node.get_children():
                    if child.kind in {CursorKind.INTEGER_LITERAL, CursorKind.FLOATING_LITERAL}:
                        var_value = float(extract_code(child)) if '.' in extract_code(child) else int(extract_code(child))
                    elif child.kind == CursorKind.UNEXPOSED_EXPR:
                        var_value = extract_code(child)

                # Assign memory address
                addresses = f"0x{address_base:06x}"
                address_base += 4  # Increment by type size (default 4 bytes)

            # Store the variable in memory_data
            memory_data.append({
                "variable": var_name,
                "value": var_value,
                "type": var_type,
                "address": addresses
            })

        # Recursively visit children
        for child in node.get_children():
            visit_node(child)

    # Start parsing the code by visiting the root node
    visit_node(translation_unit.cursor)

    # Return the parsed memory data
    return memory_data

def read_gdb_output_thread(stdout, output_queue):
    """Read GDB output in a separate thread."""
    timeout=10
    start_time = time.time()
    while True:
        try:
            if time.time() - start_time > timeout:
                print("Timeout reached, stopping reading GDB output.")
                break
            line = stdout.readline()
            if line == '': 
                break
            output_queue.put(line)
        except wexpect.wexpect_util.TIMEOUT:
            print("Timeout occurred while reading GDB output. Retrying...")
            continue
        except Exception as e:
            print(f"Unexpected error while reading GDB output: {e}")
            break

def collect_output_from_queue(output_queue):
    """Collect all lines from the output queue."""
    output = []
    while not output_queue.empty():
        output.append(output_queue.get())
    return "".join(output)


def extract_current_line(output):
    """Extract the current line of execution."""
    for line in output.splitlines():
        if "at" in line and "line" in line:
            return line.strip()
    return None


def extract_function_name(output):
    """Extract the function name from GDB output."""
    for line in output.splitlines():
        if " at " in line and "," in line:
            parts = line.split(",")
            if len(parts) > 1 and " at " in parts[1]:
                function_part = parts[1].strip()
                if "(" in function_part and ")" in function_part:
                    return function_part.split("(", 1)[0].strip()
    return None

count = 1
def get_address(gdb_process, variable):
    global count
    gdb_process.sendline(f"print &{variable}")
    while True:

        line = gdb_process.before
        # print(line)

        if line.startswith(f"${count}"):
            output = line
            count += 1
            break
        
    
    address = line.split("0x")[-1]
    return f"0x{address.strip()}" 
    return address


def extract_memory_state(gdb_process, output):
    """Extract local variables and their values from GDB output."""
    """
        The `memory_state` dictionary holds the current state of variables in memory. Each key-value pair in the dictionary represents a variable's name and its corresponding information.

        Structure:
        {
            'variable_name': (value, address)
        }

        - `variable_name`: A string representing the name of the variable in the C program (e.g., 'a', 'x', 'b', etc.).
        - `value`: A string representing the current value of the variable. This could be an integer, floating-point number, array, or any other type.
        - `address`: A string representing the memory address where the variable is stored. The address is shown as a hexadecimal string (e.g., '0x61ff1c') or may include additional context like the function or location of the address in some cases (e.g., '0x4019db <__do_global_ctors+43>').

        Example:
            {
                'a': ('2920448', '0x61ff1c'),
                'x': ('0', '0x61ff1c'),
                'y': ('7286096', '0x61ff1c'),
                'b': ('5.88661943e-039', '0x61ff18'),
                'n1': ('{-2, 6422280, 1990296173, 4200832, 6422356}', '0x61ff14'),
                'ptr': ('0x4019db <__do_global_ctors+43>', '0x61ff10')
            }

        Notes:
            - The value is a string representation of the variable's current state (e.g., numeric value, array content, or function address).
            - The address is always represented as a hexadecimal string prefixed by "0x", indicating the memory location.
            -  Some addresses may include additional debugging information (e.g., function names, offsets).
        """
    memory_state = {}
    lines = output.splitlines()

    for line in lines:
        # Skip lines starting with "(gdb)" or containing code like "4    int a",
        # or containing eip or stack trace information
        if line.startswith("(gdb)") and "=" not in line:
            continue
        if "int " in line or line.startswith("4\t") or "eip" in line:
            continue

        if line.startswith("(gdb)") and "=" in line:
            line = line[len("(gdb)"):].strip()

        # Filter out lines that don't contain "=" (skip non-variable lines)
        if "=" in line:
            try:
                var_name, var_value = line.split("=", 1)
                var_name = var_name.strip()
                var_value = var_value.strip()
                if '<__do_global_' in var_value:
                    var_value = var_value.split()[0]
                if '.' in var_value and '{' not in var_value:
                    var_value = float(var_value)
                    var_value = format(var_value,".3f")
                address = get_address(gdb_process, var_name)
                if '{' in var_value:
                    address = int(address, 16)  # Convert hex address to an integer
                    address = [hex(address + (i * 4)) for i in range(len(var_value))]
                memory_state[var_name] = var_value, address
                print(memory_state)
            except ValueError:
                continue  # Skip lines that don't split correctly

    return memory_state
