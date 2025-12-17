/* eslint-disable */
/* HELPFUL functions to call */

function restRequest(requestType, data, callback = (r) => {
    console.log('Fetch Success', r);
}, endpoint = '/api/rest') {
    const requestData = requestType === 'GET' ?
        {method: requestType, headers: {'Content-Type': 'application/json'}} :
        {method: requestType, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)}

    fetch(endpoint, requestData)
        .then((response) => {
            if (!response.ok) {
                throw (response.statusText);
            }
            return response.text();
        })
        .then((text) => {
            try {
                callback(JSON.parse(text));
            } catch {
                callback(text);
            }
        })
        .catch((error) => console.error(error));
}

function apiV2(requestType, endpoint, body = null, jsonRequest = true) {
    let requestBody = { method: requestType };
    if (jsonRequest) {
        requestBody.headers = { 'Content-Type': 'application/json' };
        if (body) {
            requestBody.body = JSON.stringify(body);
        }
    } else {
        if (body) {
            requestBody.body = body;
        }
    }

    return new Promise((resolve, reject) => {
        fetch(endpoint, requestBody)
            .then((response) => {
                if (!response.ok) {
                    reject(response.statusText);
                }
                return response.text();
            })
            .then((text) => {
                try {
                    resolve(JSON.parse(text));
                } catch {
                    resolve(text);
                }
            });
    });
}

/**
 * Given list of abilities, returns list filtered by the following
 * @param abilities {object[]} - List of abilities to be filtered
 * @param searchTerm {string} - Search query keyword
 * @param tactic {string} - Tactic name
 * @param technique {object} - Technique ID and name
 * @param platforms {string[]} - List of ability platforms
 * @param plugins {string} = Ability plugin
 * @param executors {string[]} - List of ability executors
 * @returns {object[]} - List of filtered abilities
 */
function getFilteredAbilities(abilities, searchTerm, tactic, technique, platforms = null, plugins = '', executors = null) {
    return abilities.filter((ability, index) => {
        let matchesQuery = (
            ability.name.toLowerCase().includes(searchTerm) ||
            ability.description.toLowerCase().includes(searchTerm) ||
            ability.tactic.toLowerCase().includes(searchTerm) ||
            ability.technique_id.toLowerCase().includes(searchTerm) ||
            ability.technique_name.toLowerCase().includes(searchTerm)
        );
        let matchesTactic = (!tactic || ability.tactic === tactic);
        let matchesTechnique = (!technique || `${ability.technique_id} | ${ability.technique_name}` === technique);
        let abilityPlatforms = ability.executors.map((exec) => exec.platform);
        let matchesPlatform = (!platforms) || abilityPlatforms.some((platform) => platforms.includes(platform));
        if (executors) matchesPlatform = matchesPlatform || ability.executors.some((exec) => executors.includes(exec.name));
        let matchesPlugin = (!plugins || !plugins.includes(ability.plugin));

        return matchesQuery && matchesTactic && matchesTechnique && matchesPlatform && matchesPlugin;
    });
}

/**
 * Month abbreviations for date formatting
 * @constant {string[]}
 */
const MONTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/**
 * Time constants in seconds for relative time calculations
 * @constant {Object}
 */
const TIME_UNITS = {
    MINUTE: 60,
    HOUR: 60 * 60,
    DAY: 60 * 60 * 24
};

/**
 * Parse timestamp into human-friendly date format
 * Modified from original code: https://stackoverflow.com/questions/7641791/javascript-library-for-human-friendly-relative-date-formatting
 * @param date {string} - i.e. '2021-08-03 19:37:08'
 * @returns {string} (i.e.) '5 hrs ago';
*                    (i.e. if older than 1 day): 'yesterday 10:03:23';
 *                   (i.e. if older than 2 days): 'Aug 25 10:03:23'
 */
function getHumanFriendlyTime(date) {
    if (!date) return '';
    let split = date.split('-');

    let monthIndex = Number(split[1]) - 1;
    let hDate = Number(split[2].split(' ')[0]);
    let hTime = split[2].split(' ')[1].split(':');

    const givenDate = Date.UTC(split[0], monthIndex, hDate, hTime[0], hTime[1], hTime[2]);
    // Make a fuzzy time
    let delta = Math.round((Date.now() - givenDate) / 1000);

    let fuzzy;

    if (delta < 30) {
        fuzzy = 'just now';
    } else if (delta < TIME_UNITS.MINUTE) {
        fuzzy = delta + ' seconds ago';
    } else if (delta < 2 * TIME_UNITS.MINUTE) {
        fuzzy = 'a minute ago'
    } else if (delta < TIME_UNITS.HOUR) {
        fuzzy = Math.floor(delta / TIME_UNITS.MINUTE) + ' min ago';
    } else if (Math.floor(delta / TIME_UNITS.HOUR) === 1) {
        fuzzy = '1 hr ago'
    } else if (delta < TIME_UNITS.DAY) {
        fuzzy = Math.floor(delta / TIME_UNITS.HOUR) + ' hrs ago';
    } else if (delta < TIME_UNITS.DAY * 2) {
        fuzzy = 'yesterday ' + (hTime.join(':'));
    } else {
        const monthName = MONTH_NAMES_SHORT[monthIndex] || '';
        fuzzy = monthName + ' ' + hDate + ' ' + hTime.join(':');
    }
    return fuzzy;
}

/**
 * Parse timestamp into human-friendly date ISO8601-safe format
 * @param dateTime {string} - Expected ISO8601 input in UTC time: (i.e.) 2021-08-25T10:03:23Z
 * @returns {string} - (i.e.) '5 hrs ago'
 */
function getHumanFriendlyTimeISO8601(dateTime) {
	return getHumanFriendlyTime(dateTime.replace('T', ' ').replace('Z', ''));
}

function sortAlphabetically(list) {
    return list.sort((a, b) => {
        let x = a.toLowerCase(), y = b.toLowerCase();
        if (x < y) return -1;
        else if (x > y) return 1;
        else return 0;
    })
}

function sanitize(unsafeMsg) {
    const parser = new DOMParser();
    let doc = parser.parseFromString(unsafeMsg, 'text/html');
    return doc.body.innerText;
}

function toast(message, success) {
    bulmaToast.toast({
        message: `<span class="icon"><i class="fas fa-${success ? 'check' : 'exclamation'}"></i></span> ${sanitize(message)}`,
        type: `toast ${success ? 'is-success' : 'is-danger'}`,
        position: 'bottom-right',
        duration: '3000',
        pauseOnHover: true
    });
}

function validateInputs(obj, requiredFields) {
    let fieldErrors = [];
    requiredFields.forEach((field) => {
        if (obj[field].length === 0) {
            fieldErrors.push(field);
        }
    });

    return fieldErrors;
}

function downloadJson(filename, data) {
    let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
    let downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", filename + ".json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

function downloadReport(endpoint, filename, data = {}, jsonifyData = false) {
    function downloadObjectAsJson(data) {
        stream('Downloading report: ' + filename);
        const parsedData = jsonifyData ? JSON.stringify(data, null, 2) : data;
        let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(parsedData);
        let downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", filename + ".json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    }

    restRequest('POST', data, downloadObjectAsJson, endpoint);
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/* SECTIONS */

// Alternative to JQuery parseHTML(keepScripts=true)
function setInnerHTML(elem, html) {
    elem.innerHTML = html;
    const scripts = Array.from(elem.querySelectorAll("script"));
    if (scripts) {
        scripts.forEach(oldScript => {
            const newScript = document.createElement("script");
            Array.from(oldScript.attributes)
                .forEach( attr => newScript.setAttribute(attr.name, attr.value) );
            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }
}


// TODO: remove this from all individual plugins in future, as close (x) will be in the tab rather than inside the plugins itself
function removeSection(identifier) {
    $('#' + identifier).remove();
}

function b64DecodeUnicode(str) { //https://stackoverflow.com/a/30106551
    if (str != null) {
        // An error check is needed in case the wrong codec (i.e. not UTF-8) was used at source
        try {
            return decodeURIComponent(atob(str).split('').map(function (c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
        } catch {
            return atob(str);
        }
    } else return "";
}

