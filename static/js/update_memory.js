let currentLine = null;
let memoryData = [];
let debuggingSessionStarted = false; // Track if the session has started
let highlightedLine = null; /// Track if the session has started

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
            console.log(currentLine)
            memoryData = data.memory_state;
            updateVisualization();
        } catch (error) {
            console.error("Error in stepForward:", error);
        }
    }

    function updateVisualization() {
        document.getElementById("code-input").textContent = `Current Line: ${currentLine}`;
        visualizeMemoryLine(memoryData);
        // Highlight the current line in the CodeMirror editor
        if (currentLine !== null) {
            const lineIndex = currentLine - 1;
    
            if (highlightedLine !== null) {
                editor.removeLineClass(highlightedLine, "background", "line-highlight");
            }
            
            editor.addLineClass(lineIndex, "background", "line-highlight");
            highlightedLine = lineIndex;
    
            // Scroll to the highlighted line
            editor.scrollIntoView({ line: lineIndex, ch: 0 }, 100); // Smooth scrolling
        }
    }

    // Event listeners for the buttons
    document.getElementById("next-button").addEventListener("click", stepForward);
    document.getElementById("start-btn").addEventListener("click", startDebugging);
    document.getElementById("stop-btn").addEventListener("click", stopDebugging);
});
// Function to visualize memory
// Function to visualize memory
function visualizeMemoryLine(memoryData) {
    const svg = d3.select("#memory-svg");
    const blockHeight = 50;
    const blockWidth = 150;
    const padding = 10;

    // Get the number of existing blocks to calculate the starting y-position
    const existingBlocks = svg.selectAll("rect").size();
    let startY = existingBlocks * (blockHeight + padding);

    memoryData.forEach((block, i) => {
        const y = startY + i * (blockHeight + padding); // Calculate the y-position for new blocks

        // Draw rectangle
        svg.append("rect")
            .attr("x", 50)
            .attr("y", y)
            .attr("width", blockWidth)
            .attr("height", blockHeight)
            .attr("fill", "#e0f7fa")
            .attr("stroke", "#00796b");

        // Variable name (outside the box on the left)
        svg.append("text")
            .attr("x", 30) // Position outside the left side of the rectangle
            .attr("y", y + blockHeight / 2 + 5)
            .text(block.variable)
            .attr("font-size", "14px")
            .attr("font-family", "monospace")
            .attr("text-anchor", "end"); // Align text to the right

        // Value (centered in the rectangle)
        svg.append("text")
            .attr("x", 50 + blockWidth / 2)
            .attr("y", y + blockHeight / 2 + 5)
            .text(block.value)
            .attr("font-size", "14px")
            .attr("font-family", "monospace")
            .attr("text-anchor", "middle");

        // Address (outside the box on the right)
        svg.append("text")
            .attr("x", 50 + blockWidth + 10) // Position outside the right side of the rectangle
            .attr("y", y + blockHeight / 2 + 5)
            .text(block.address)
            .attr("font-size", "12px")
            .attr("font-family", "monospace")
            .attr("text-anchor", "start"); // Align text to the left
    });
}
