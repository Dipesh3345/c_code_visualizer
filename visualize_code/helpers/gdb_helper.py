from .memory_helper import read_gdb_output,parse_gdb_output,extract_current_line
import subprocess
import json

class GDBSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.gdb_process = None
        self.current_line = None
        self.memory_state = []
        self.function_name = None
        self.history = []
        self.count = 0

    def start_debugging(self, c_code):
        try:
            if not c_code.strip():
                return {"error": "No C code provided."}

            # Save and compile the C code
            with open('temp.c', 'w') as file:
                file.write(c_code)

            compile_result = subprocess.run(
                ['gcc', '-g', '-O0', 'temp.c', '-o', 'temp.out'], 
                capture_output=True, text=True
            )
            if compile_result.returncode != 0:
                return {"error": compile_result.stderr}

            # Start GDB process
            self.gdb_process = subprocess.Popen(
                ['gdb', './temp.out'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Set breakpoint and run program
            self.gdb_process.stdin.write("break temp.c:1\n")
            self.gdb_process.stdin.write("run\n")
            self.gdb_process.stdin.write("info frame\n")
            self.gdb_process.stdin.flush()

            return {"message": "Debugging session started."}
        except Exception as e:
            return {"error": str(e)}

    def step_forward(self):
        try:
            if not self.gdb_process:
                return {"error": "Debugging session not started."}

            # Step forward in GDB
            self.gdb_process.stdin.write("next\n")
            self.gdb_process.stdin.flush()

            # Read and process GDB output
            gdb_output = read_gdb_output(self.gdb_process, self.count)
            self.count += 1

            if not gdb_output:
                return {
                    "current_line": None,
                    "function_name": None,
                    "memory_state": {},
                    "status": "completed"
                }

            # Extract details
            current_line = gdb_output.get("matched_line")
            if not self.function_name:
                self.function_name = gdb_output.get("function_name")
            memory_state = parse_gdb_output(current_line) if current_line else {}
            print(f"Memory State SF: {memory_state}")

            current_line = extract_current_line(current_line)
            # Update session state
            self.current_line = current_line
            self.memory_state = memory_state
            self.history.append({
                "line": current_line,
                "memory_state": memory_state
            })

            return {
                "current_line": current_line,
                "memory_state": memory_state,
                "function_name": self.function_name,
                "status": "running"
            }
        except Exception as e:
            return {"error": str(e)}

    def stop_debugging(self):
        try:
            if self.gdb_process:
                self.gdb_process.terminate()
                return {"message": "Debugging session ended."}
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
