// Step 1: On the Thomann search page, open up your browser's developer tools (F12) and navigate to console.
// Step 2: In PART 1 below, change the value of stringToLookFor to match what you are looking for.
    // Note: This is case-sensitive. I was looking for "aluminum" so searched for "luminum" to include "Aluminum" results too.
// Step 3: Copy PART 1 and 2 into the console; press enter.
// Step 4: Copy PART 3 into the console; press enter (this is separated from step 3 as it requires a short wait)
// Step 5: Enter "openNextPages()" as many times as required until you have worked through all matches.


// PART 1:
// The string you are looking for
var stringToLookFor = 'luminum';

// How many pages to open each time (decrease if your computer struggles with lots of tabs)
var numPagesAtATime = 20;


// PART 2:
// Copy and paste this section into console
var jq = document.createElement('script');
jq.src = "https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js";
document.getElementsByTagName('head')[0].appendChild(jq);

var matches = [];
var counter = 0;


// PART 3:
$("textarea").map( function() {
    if ($(this).val().indexOf( stringToLookFor ) != -1) {
        matches.push(this);
    }
});

function openNextPages(currentCount = counter) {
    for (match of matches.slice(currentCount, currentCount + numPagesAtATime)) {
        $(match).next()[0].click()
    };

    counter += numPagesAtATime;
}

console.log("Found " + matches.length + " matches. Use `openNextPages()` repeatedly to open " + numPagesAtATime + " pages at a time.")
