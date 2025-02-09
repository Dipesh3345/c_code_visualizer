    """Run debugging session."""
        self.send_gdb_command("break main")

        # Set the working directory to where the source file is located (if needed)
        self.send_gdb_command("cd F:/c_code_visualizer")  # Replace with your actual source file path
        self.send_gdb_command("directory F:/c_code_visualizer")  # Optional: Make sure GDB knows where the source is

        # Wait until the breakpoint is set
        output = self.collect_output(expected_text="Breakpoint")
        print("Output after setting breakpoint:\n", output)

        self.send_gdb_command("run")

        # Wait for the program to hit the breakpoint
        output = self.collect_output(expected_text="Breakpoint")
        print("Output after run:\n", output)

        # Now send "info locals" after ensuring the breakpoint is hit
        self.send_gdb_command("info locals")
        locals_output = self.collect_output(expected_text="(gdb)")
        print("Local variables:\n", locals_output)
