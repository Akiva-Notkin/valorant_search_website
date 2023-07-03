// When the form is submitted, validate the JSON data before submitting the form

const link = document.getElementById('update_link');

// URL encode textarea value to ensure it's safe to include in a URL
function urlEncode(value) {
    return encodeURIComponent(value).replace(/%20/g, '+');
}

function stripSpaces(value) {
    return value.replace(/\s/g, '');
}

function createLocalLinks(json_dictionary) {
    var path = window.location.pathname + '?'
    for (let [key, value] of Object.entries(json_dictionary)) {
        path += key + '=' + urlEncode(stripSpaces(value)) + '&';
    }
    link.href = path;
    link.textContent = 'https://valorantvodsearcher.com' + path;
}

window.onload = function () {
    // Update the link when the page loads
    const json_elements = document.getElementsByClassName('json_data');
    const json_dictionary = {};

    for (var i = 0; i < json_elements.length; i++) {
        json_dictionary[json_elements[i].id] = json_elements[i].value;
        json_elements[i].addEventListener('input', function() {
            json_dictionary[this.id] = this.value;
        });

        json_elements[i].addEventListener('input', function () {
            // Update the link when the textarea content changes
            createLocalLinks(json_dictionary);
        });
    }

    createLocalLinks(json_dictionary);
    let myForm = document.getElementById('myForm');
    myForm.addEventListener('submit', function (event) {
        event.preventDefault();

        try {
            for (var i = 0; i < json_elements.length; i++) {
                JSON.parse(json_elements[i].value);
            }
            HTMLFormElement.prototype.submit.call(myForm);
        } catch (e) {
            alert('Invalid JSON data' + e);
        }
    });
};