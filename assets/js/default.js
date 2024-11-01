---
---
; // Ignore this error, this is a liquid-javascript file, but I want the intellisense to still work, which Liquid breaks/disables/Idunno

/**
 * @type {string} The base url of the website, '' for local hosting, should be the name of the repo when hosted on GitHub
 */
const baseURL = `{{ site.baseurl }}`

/**
 * @type {string} The current game version being used, used to navigate to correct folder of items
 */
const gameVersion = `{{ page.version }}`

const URL_params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
});

/**
 * @param {String} path
 * @param {String} extension
 * @return {String}
 */
function url_to (path, extension) {
    let dir;
    if (extension == 'png' || extension == 'jpg') dir = 'images';
    else dir = extension;
    return `{{ site.baseurl }}/assets/${dir}/${path}.${extension}`
}
