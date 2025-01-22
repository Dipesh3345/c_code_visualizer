import re

def parse_gdb_output(output):
    memory_data = []
    address_base = 0x1000  # Starting address for memory allocation (mocked for demonstration)
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
            array_type = array_match.group(1).strip()
            array_name = array_match.group(2).strip()
            # Extract values if provided; otherwise, initialize with default values
            values_str = array_match.group(3).strip()
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

    return memory_data

# Test the function
print(parse_gdb_output(' 5      int b[5] = {};'))
