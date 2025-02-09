from .memory_helper import extract_current_line, parse_with_clang, extract_function_name, extract_memory_state
import subprocess
import json
import threading
import queue
import wexpect
import time
import os

import subprocess
import wexpect
import queue
import threading
import time

class GDBSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.gdb_process = None
        self.current_line = None
        self.memory_state = []
        self.function_name = None
        self.history = []
        self.output_queue = queue.Queue()
        self.thread = None
        self.stop_event = threading.Event()

    def read_gdb_output_thread(self):
        """Continuously read GDB output and store it in the queue."""
        while not self.stop_event.is_set():
            try:
                index = self.gdb_process.expect(["\r\n", wexpect.EOF, wexpect.TIMEOUT], timeout=2)
                if index == 0:  # New line received
                    line = self.gdb_process.before.strip()
                    if line:
                        self.output_queue.put(line)
                elif index == 1:  # EOF received, GDB exited
                    print("GDB process has exited.")
                    self.stop_event.set()  # Stop the thread
                    break
            except wexpect.TIMEOUT:
                continue
            except Exception as e:
                print(f"Unexpected error in GDB thread: {e}")
                self.stop_event.set()  # Stop the thread on error
                break

    def collect_output(self, expected_text="(gdb)", timeout=5):
        """Collect GDB output until expected text is found or timeout occurs."""
        output = []
        start_time = time.time()

        while True:
            try:
                if time.time() - start_time > timeout:
                    print("Timeout while waiting for GDB output.")
                    break

                line = self.output_queue.get(timeout=0.5)
                output.append(line)

                # Stop if we see "(gdb)" on a new line
                if line.strip() == expected_text:
                    break  

            except queue.Empty:
                break

        return "\n".join(output)

    def start_debugging(self, c_code):
        try:
            self.gdb_process = None
            if not c_code.strip():
                return {"error": "No C code provided."}

            # Save and compile the C code
            with open('test_temp.c', 'w') as file:
                file.write(c_code)

            compile_result = subprocess.run(
                ['gcc', '-g', 'test_temp.c', '-o', 'test_temp.out'], 
                capture_output=True, text=True
            )

            if compile_result.returncode != 0:
                return {"error": compile_result.stderr}

            # Start GDB
            self.gdb_process = wexpect.spawn('gdb ./test_temp.out')
            self.gdb_process.sendline("set pagination off")

            # Start output reading thread
            self.thread = threading.Thread(target=self.read_gdb_output_thread)
            self.thread.daemon = True
            self.thread.start()

            # Set breakpoint at main
            self.gdb_process.sendline("break main")
            output = self.collect_output(expected_text="Breakpoint")
            print("Output after setting breakpoint:\n", output)

            # Run the program
            self.gdb_process.sendline("run")
            output = self.collect_output(expected_text="Breakpoint")
            print("Output after run:\n", output)

            # Get current line information
            self.gdb_process.sendline("info line")
            line_output = self.collect_output()
            print("Line info:\n", line_output)

            # Get local variables
            self.gdb_process.sendline("info locals")
            locals_output = self.collect_output()
            print("Local variables:\n", locals_output)

            # Extract current line and function name
            self.current_line = extract_current_line(line_output)
            self.function_name = extract_function_name(line_output)
            self.memory_state = extract_memory_state(self.gdb_process, locals_output)

            return {
                "current_line": 1,
                "function_name": "main",
                "memory_state": self.memory_state,
                "status": "running"
            }
        except Exception as e:
            return {"error": str(e)}


    def step_forward(self):
        try:
            if not self.gdb_process:
                return {"error": "Debugging session not started."}

            print("1")
            self.gdb_process.sendline("next")

            # Collect output after "next"
            next_output = self.collect_output(expected_text="(gdb)", timeout=5)
            print("2", next_output)

            # Send "info locals" to get variable states
            self.gdb_process.sendline("info locals")
            locals_output = self.collect_output(expected_text="(gdb)", timeout=5)
            print("3", locals_output)  # Debug output

            # Ensure we received output
            if not locals_output.strip():
                return {
                    "current_line": None,
                    "function_name": None,
                    "memory_state": {},
                    "status": "completed"
                }

            # Extract details
            current_line = extract_current_line(next_output)
            print(f"Current Line: {current_line}")

            if not self.function_name:
                self.function_name = extract_function_name(next_output)

            memory_state = extract_memory_state(self.gdb_process, locals_output)
            print(f"Memory State SF: {memory_state}")

            # Update session state
            self.current_line = current_line
            self.memory_state = memory_state
            self.history.append({
                "line": current_line,
                "memory_state": memory_state
            })

            return {
                "current_line": 1,
                "function_name": "main",
                "memory_state": self.memory_state,
                "status": "running"
            }

        except Exception as e:
            return {"error": str(e)}



    def stop_debugging(self):
        try:
            if self.gdb_process:
                # Tell GDB to exit
                self.gdb_process.sendline("quit")
                self.gdb_process.close()  # Properly close GDB session

                # Stop the output reading thread
                self.stop_event.set()
                if self.thread:
                    self.thread.join(timeout=2)  # Ensure thread stops

                # Cleanup temporary file
                if os.path.exists("test_temp.c"):
                    os.remove("test_temp.c")

                return {"message": "Debugging session ended successfully."}
            
            return {"error": "No active debugging session found."}
        
        except Exception as e:
            return {"error": str(e)}

# Global Dictionary to Manage Sessions
gdb_sessions = {}

def start_debugging_session(request):
    session_id = request.session.session_key or request.session.save()
    data = json.loads(request.body)
    c_code = data.get('c_code', '')

    session = GDBSession(session_id)
    gdb_sessions[session_id] = session
    print(gdb_sessions)
    return session.start_debugging(c_code)

def step_forward_session(request):
    session_id = request.session.session_key
    session = gdb_sessions.get(session_id)
    if session:
        return session.step_forward()
    return {"error": "Session not available."}

def stop_debugging_session(request):
    session_id = request.session.session_key
    session = gdb_sessions.pop(session_id, None)
    if session:
        return session.stop_debugging()
    return {"error": "Session not available."}
