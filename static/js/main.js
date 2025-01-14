// Initialize CodeMirror on the textarea
var editor = CodeMirror.fromTextArea(document.getElementById('code-input'), {
    lineNumbers: true,       // Enable line numbers
    mode: "text/x-csrc",     // Set syntax highlighting for C
    theme: "monokai",        // Set a theme (e.g., monokai)
    indentUnit: 4,           // Set indentation to 4 spaces
    lineWrapping: true,      // Enable line wrapping
    matchBrackets: true,     // Highlight matching brackets
    readOnly: false          // Ensure the editor is editable (default is false)
});

// Clear editor function
function clearEditor() {
    editor.setValue("");
}

// Handle button events
document.addEventListener("DOMContentLoaded", () => {
    const runCodeBtn = document.getElementById("run-code-btn");
    const visualizeMemoryBtn = document.getElementById("visualize-memory-btn");
    const form = document.getElementById("code-form");

    runCodeBtn.addEventListener("click", () => {
        const existingInput = document.querySelector("input[name='action']");
        if (existingInput) existingInput.remove();

        const actionInput = document.createElement("input");
        actionInput.type = "hidden";
        actionInput.name = "action";
        actionInput.value = "run_code";
        form.appendChild(actionInput);
        form.submit();
    });

    visualizeMemoryBtn.addEventListener("click", () => {
        const existingInput = document.querySelector("input[name='action']");
        if (existingInput) existingInput.remove();

        const actionInput = document.createElement("input");
        actionInput.type = "hidden";
        actionInput.name = "action";
        actionInput.value = "visualize_memory";
        form.appendChild(actionInput);
        form.submit();
    });
});

// Function to visualize memory
function visualizeMemory(memoryData) {
    const svg = d3.select("#memory-svg");
    const blockHeight = 50;
    const blockWidth = 150;

    // Clear previous visualization
    svg.selectAll("*").remove();

    memoryData.forEach((block, i) => {
        const y = i * (blockHeight + 10);

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


// Get memory data from the template
document.addEventListener("DOMContentLoaded", () => {
    const memoryData = JSON.parse(document.getElementById("memory_data").textContent);
    visualizeMemory(memoryData);
});

