/*
Function to pull all data from LoLdle and download it as a CSV file.
This script is intended to be run in the browser console on the LoLdle page.

Instructions: 
You have to find the current Champion of the day, then guess every champion other than the correct one, then use this script to download the updated data.

*/

(function() {
    function downloadCSV(csv, filename) {
        let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        let link = document.createElement("a");
        if (link.download !== undefined) { 
            let url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    function extractData() {
        let container = document.querySelector(".answers-container.classic-answers-container");
        if (!container) {
            console.error("Container not found!");
            return;
        }

        let answers = container.querySelectorAll(".classic-answer");
        let data = [];

        // Header row for CSV
        let headers = ["Champion Name, Gender, Position(s), Species, Resource, Range Type, Region(s), Release Year"];
        data.push(headers.join(","));

        // Extract data from each classic-answer div
        answers.forEach((answer, index) => {
            answer = answer.querySelector(".square-container")
            let row = []; // Start with the answer index
            nameVal = answer.querySelector(".square")
            if(nameVal){
                nameText = nameVal.querySelector(".champion-icon-name").textContent.trim()
                row.push(nameText)
            }
            else{
                console.log("no name found")
            }
            for (let i = 0; i <= 6; i++) {
                // Directly query the square with 'square X'
               // Use the square class with index to find the correct square element
                let square = Array.from(answer.querySelectorAll(".square"))
                .find(sq => sq.className.includes(`square ${i}`)); // Check for class "square X"
                if (square) {
                    let mainText = square.childNodes[0]?.textContent.trim().replace(/"/g, '""') || ""; 
                    row.push(`"${mainText}"`); // Wrap the text in quotes
                } else {
                    console.log("bad row")
                    row.push(""); // Fill empty columns if square-X is missing
                }
            }

            data.push(row.join(","));
        });

        let csvContent = data.join("\n");
        downloadCSV(csvContent, "loldle_data.csv");
    }

    extractData();
})();
