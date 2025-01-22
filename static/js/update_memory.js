let currentLine = null;
let memoryData = [];
let debuggingSessionStarted = false; // Track if the session has started
let highlightedLine = null; /// Track if the session has started
const variablePositions = {};
const variableAddressMap = {};

// Get CSRF token from the meta tag
const csrfToken = document.querySelector('[name="csrf-token"]').getAttribute('content');

document.addEventListener("DOMContentLoaded", () => {
    async function startDebugging() {
        try {
            const response = await fetch('/start_debugging/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken, // Add CSRF token to the header
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    c_code: editor.getValue() // Pass the C code from CodeMirror editor
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                console.error(data.error);
                return;
            }

            debuggingSessionStarted = true; // Mark debugging session as started
            console.log("Debugging session started");
            alert("Debugging session has started. Please press Next");
        } catch (error) {
            console.error("Error in startDebugging:", error);
        }
        const svg = d3.select("#memory-svg");
        svg.selectAll("*").remove();
    }

    // Add stopDebugging function
    async function stopDebugging() {
        try {
            if (!debuggingSessionStarted) {
                alert("No debugging session to stop.");
                return;
            }

            const response = await fetch('/stop_debugging/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken, // Add CSRF token to the header
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            debuggingSessionStarted = false; // Reset debugging session flag
            console.log("Debugging session stopped");
            alert("Debugging session has been stopped.");
        } catch (error) {
            console.error("Error in stopDebugging:", error);
        }
    }

    async function stepForward() {
        try {
            // Start debugging session if not already started
            if (!debuggingSessionStarted) {
                alert("Please start debugging before stepping forward.");
                return; // Exit the function early
            }

            const response = await fetch('/step_forward/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken, // Add CSRF token to the header
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}) // Request body (you can pass data if needed)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                console.error(data.error);
                return;
            }

            currentLine = data.current_line;
            memoryData = data.memory_state;
            functionName = data.function_name;
            memoryData.forEach(value => {
                if (value !== undefined) {
                    console.log(value);
                }
            });
            updateVisualization();
        } catch (error) {
            console.error("Error in stepForward:", error);
        }
    }
    function updateVisualization() {
        // Validate editor instance
        if (!editor) {
            console.error("Error: editor instance is not initialized.");
            return;
        }
    
        // Validate currentLine
        const totalLines = editor.lineCount(); // Get the total number of lines in the editor
        if (currentLine === null || currentLine === undefined || currentLine <= 0 || currentLine > totalLines) {
            console.error(`Error: Invalid currentLine value (${currentLine}). Must be between 1 and ${totalLines}.`);
            return;
        }
    
        // Update the current line display
        document.getElementById("code-input").textContent = `Current Line: ${currentLine}`;
        visualizeMemoryLine(memoryData, functionName);
    
        // Highlight the current line in the CodeMirror editor
        const lineIndex = currentLine - 1;
    
        if (highlightedLine !== null) {
            editor.removeLineClass(highlightedLine, "background", "line-highlight");
        }
    
        editor.addLineClass(lineIndex, "background", "line-highlight");
        highlightedLine = lineIndex;
    
        // Scroll to the highlighted line
        editor.scrollIntoView({ line: lineIndex, ch: 0 }, 100); // Smooth scrolling
    }
    

    // Event listeners for the buttons
    document.getElementById("next-button").addEventListener("click", stepForward);
    document.getElementById("start-btn").addEventListener("click", startDebugging);
    document.getElementById("stop-btn").addEventListener("click", stopDebugging);
});
// Function to visualize memory
function visualizeMemoryLine(memoryData, functionName) {
    const svg = d3.select("#memory-svg");
    const blockHeight = 50;
    const blockWidth = 75;
    const padding = 25;

    // Add function name at the top if not already present
    if (svg.selectAll(".function-name").empty()) {
        svg.append("text")
            .attr("class", "function-name")
            .attr("x", 50)
            .attr("y", 30)
            .text(`Function: ${functionName}`)
            .attr("font-size", "16px")
            .attr("font-family", "monospace")
            .attr("font-weight", "bold")
            .attr("text-anchor", "start")
            .attr("fill", "#000");
    }

    // Calculate the current starting Y position dynamically
    let currentY = 60;

    // Find the height of the existing elements to append new ones below
    svg.selectAll("rect").each(function () {
        const rectY = +d3.select(this).attr("y") + blockHeight + padding;
        if (rectY > currentY) {
            currentY = rectY;
        }
    });

    // Add memory blocks dynamically
    memoryData.forEach((block) => {
        const { variable, value, type, address } = block;

        if (Array.isArray(value) && Array.isArray(address)) {
            const arrayStartX = 100; // Starting x-position for the array
            const arrayStartY = currentY;

            // Label the array name and type
            svg.append("text")
                .attr("x", arrayStartX - 10)
                .attr("y", arrayStartY + blockHeight / 2 + 5)
                .text(`${variable} (${type})`)
                .attr("font-size", "14px")
                .attr("font-family", "monospace")
                .attr("text-anchor", "end");

            // Visualize each element of the array
            value.forEach((val, idx) => {
                const x = arrayStartX + idx * (blockWidth + padding);

                // Draw a rectangle for the array element
                svg.append("rect")
                    .attr("x", x)
                    .attr("y", arrayStartY)
                    .attr("width", blockWidth)
                    .attr("height", blockHeight)
                    .attr("fill", "#e8f5e9")
                    .attr("stroke", "#388e3c");

                // Display the value inside the rectangle
                svg.append("text")
                    .attr("x", x + blockWidth / 2)
                    .attr("y", arrayStartY + blockHeight / 2 + 5)
                    .text(val)
                    .attr("font-size", "14px")
                    .attr("font-family", "monospace")
                    .attr("text-anchor", "middle");

                // Display the address below the rectangle
                svg.append("text")
                    .attr("x", x + blockWidth / 2)
                    .attr("y", arrayStartY + blockHeight + 15)
                    .text(address[idx])
                    .attr("font-size", "12px")
                    .attr("font-family", "monospace")
                    .attr("text-anchor", "middle");
            });

            // Update currentY for the next block
            currentY += blockHeight + padding;
        } else {
            // Single variable
            const y = currentY;

            // Draw rectangle
            svg.append("rect")
                .attr("x", 100)
                .attr("y", y)
                .attr("width", blockWidth)
                .attr("height", blockHeight)
                .attr("fill", "#e0f7fa")
                .attr("stroke", "#00796b");

            // Variable name
            svg.append("text")
                .attr("x", 50)
                .attr("y", y + blockHeight / 2 + 5)
                .text(variable)
                .attr("font-size", "14px")
                .attr("font-family", "monospace")
                .attr("text-anchor", "end");

            // Value
            svg.append("text")
                .attr("x", 100 + blockWidth / 2)
                .attr("y", y + blockHeight / 2 + 5)
                .text(value)
                .attr("font-size", "14px")
                .attr("font-family", "monospace")
                .attr("text-anchor", "middle");

            // Address
            svg.append("text")
                .attr("x", 100 + blockWidth + 10)
                .attr("y", y + blockHeight / 2 + 5)
                .text(address)
                .attr("font-size", "12px")
                .attr("font-family", "monospace")
                .attr("text-anchor", "start");
            
            // Store variable position for future reference
            variablePositions[variable] = {
                x: 100 + blockWidth / 2,
                y: y + blockHeight / 2
            };

            // Update the address map
            variableAddressMap[variable] = address;

            console.log(variablePositions)
            // Check if the variable is a pointer
            if (type.endsWith('*') && value !== "NULL") {
                console.log("Hello")
                // Find the referenced variable by its address
                const referencedVariable = Object.keys(variablePositions).find(
                    (key) => variableAddressMap[key] === value
                );

                if (referencedVariable) {
                    const targetPos = variablePositions[referencedVariable];
                    console.log(targetPos)
                    // Draw an arrow from the pointer to the referenced variable

                    // Add the marker definition
                    svg.append("defs")
                        .append("marker")
                        .attr("id", "arrowhead")
                        .attr("markerWidth", 10)
                        .attr("markerHeight", 7)
                        .attr("refX", 10)
                        .attr("refY", 3.5)
                        .attr("orient", "auto")
                        .append("path")
                        .attr("d", "M0,0 L10,3.5 L0,7 Z")
                        .attr("fill", "black");
                        
                    svg.append("line")
                        .attr("x1", 50 + blockWidth)
                        .attr("y1", y + blockHeight / 2 - 20)
                        .attr("x2", targetPos.x)
                        .attr("y2", targetPos.y + 20)
                        .attr("stroke", "black")
                        .attr("stroke-width", 2)
                        .attr("marker-end", "url(#arrowhead)"); // Add an arrowhead marker
                }
            }
            // Update currentY for the next block
            currentY += blockHeight + padding;
        }
    });
}