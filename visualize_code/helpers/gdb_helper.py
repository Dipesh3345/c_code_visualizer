from .memory_helper import read_gdb_output,parse_gdb_output,extract_current_line
import subprocess
import json
import time

gdb_sessions = {}

def start_debugging_session(request):
    try:
        data = json.loads(request.body)
        c_code = data.get('c_code', '').strip()

        if not c_code:
            return {"error": "No C code provided."}

        session_id = request.session.session_key or request.session.save()

        # Save and compile the C code
        with open('temp.c', 'w') as file:
            file.write(c_code)

        compile_result = subprocess.run(['gcc', '-g', 'temp.c', '-o', 'temp.out'], capture_output=True, text=True)
        if compile_result.returncode != 0:
            return {"error": compile_result.stderr}

        # Start GDB process
        gdb_process = subprocess.Popen(
            ['gdb', './temp.out'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Initialize the session in the global gdb_sessions
        gdb_sessions[session_id] = {
            "process": gdb_process,
            "current_line": None,
            "memory_state": [],
            "history": []
        }

        # Set breakpoint at the start of main and run the program
        gdb_process.stdin.write("break temp.c:1\n")
        gdb_process.stdin.write("run\n")
        gdb_process.stdin.flush()

        return {"message": "Debugging session started."}

    except Exception as e:
        return {"error": str(e)}  # Ensure that we return a dictionary for errors

def step_forward_session(request):
    try:
        session_id = request.session.session_key
        if not session_id:
            return {"error": "Session not available."}

        gdb_session = gdb_sessions.get(session_id)
        if not gdb_session:
            return {"error": "Debugging session not started."}

        gdb_process = gdb_session["process"]

        # Execute the 'next' command in GDB to step forward
        gdb_process.stdin.write("next\n")
        gdb_process.stdin.flush()

        # Add a small delay to ensure GDB has time to process
        time.sleep(0.1)

        # Read the output after stepping forward
        output = read_gdb_output(gdb_process)

        if not output:
            return {
                "current_line": None,
                "memory_state": {},
                "status": "completed"
            }

        current_line = extract_current_line(output)
        memory_state = parse_gdb_output(output)

        # Update session state
        gdb_session["current_line"] = current_line
        gdb_session["memory_state"] = memory_state
        gdb_session["history"].append({
            "line": current_line,
            "memory_state": memory_state
        })

        return {
            "current_line": current_line,
            "memory_state": memory_state,
            "status": "running"
        }

    except Exception as e:
        return {"error": str(e)}  # Ensure that we return a dictionary for errors

def stop_debugging_session(request):
    try:
        session_id = request.session.session_key
        gdb_session = gdb_sessions.pop(session_id, None)
        
        if gdb_session and gdb_session["process"]:
            gdb_session["process"].terminate()
            return {"message": "Debugging session ended."}
        
        return {"error": "No active debugging session found."}
    
    except Exception as e:
        return {"error": str(e)}  # Ensure we return a dictionary for errors
