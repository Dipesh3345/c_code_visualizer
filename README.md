
# Project Title

C Code Visualizer is a web-based application that allows users to interactively visualize C code execution. Users can step through their code line by line, view memory allocation, and understand how variables and values change during execution.


## Features

- Interactive stepping through C code
- Visualize memory: variable names, values, and addresses
- Error feedback for compilation and runtime issues

## Installation

Install c_code_visualizer with Django

```bash
    git clone https://github.com/pravinsang/c_code_visualizer.git
    cd c_code_visualizer
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver
    Open your browser and navigate to http://127.0.0.1:8000
```
## Usage

### Writing and Running Code
1. **Enter your C code**: Use the editor on the homepage to write your C code.
2. **Run or Visualize**:
   - Click **Run Code** to compile and execute your code.
   - Click **Visualize Memory** to start a debugging session and analyze memory.

### Debugging
1. **Start Debugging**: Click the **Start Debugging** button to initialize a debugging session.
2. **Step Through Code**:
   - Use the **Next Step** button to execute your code line by line.
   - Watch the memory visualization update in real-time.
3. **Stop Debugging**: Click the **Stop Debugging** button to terminate the debugging session.

## API Reference
| API Endpoint       | HTTP Method | Description                |
| :----------------- | :---------: | :------------------------- |
| `/start_debugging` | POST        | Starts a debugging session |
| `/step_forward`    | POST        | Moves to the next step     |
| `/stop_debugging`  | POST        | Stops the debugging session|

#### Example JavaScript Call
```javascript
fetch('/start_debugging', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ c_code: 'int a = 10; printf("%d", a);' }),
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));

```


## Folder Structure

### `c_code_visualizer/` (Root Directory)
- **manage.py**
- **db.sqlite3**
- **README.md**
  
### `visualize_code/` (Main App Folder)
- **`__init__.py`**
- **admin.py**
- **apps.py**
- **helpers/**
  - **gdb_helpers.py**
  - **memory_helpers.py**
- **migrations/**
  - **`__init__.py`**
- **models.py**
- **templates/**
  - **home.html**: Homepage template.
- **tests.py**
- **urls.py**
- **views.py**

### `static/` (Static Files)
- **css/**
  - **style.css**
- **js/**
  - **update_memory.py**
  - **main.js**
  
## Screenshots

### Homepage
![Homepage Screenshot](images/screenshot2.png)

### Debugger View
![Debugger Screenshot](images/screenshot1.png)