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
    if (extension == 'png' || extension == 'jpg' || extension=='svg') dir = 'images'
    else dir = extension;
    return `{{ site.baseurl }}/assets/${dir}/${path}.${extension}`
}

/**
 * Returns an html element for displaying the icon with the given `name`
 * @param {string} name File name for the svg to use, stored in assets/images/icons
 * @param {string[]} [classes=[]] Any class names to pass to the svg element
 * @returns {string} The html result
 */
function icon (name, classes=[]) {
    return `<svg class="feather ${classes.join(' ')}">
        <use href="${url_to('feather-sprite', 'svg')}#${name}"/>
    </svg>`;
}
