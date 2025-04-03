
--- // eslint-disable-line expression-expected -- Ignore liquid syntaxll
---

; // Ignore this error, this is a liquid-javascript file, but I want the intellisense to still work, which Liquid breaks/disables/Idunno

/* eslint-disable */
/* eslint-enable */
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck
// @ts-ignore
/* jshint ignore:start */
/* jshint ignore:end */



/**
 * @type {string} The base url of the website, '' for local hosting, should be the name of the repo when hosted on GitHub
 */
const baseURL = `{{ site.baseurl }}`;

/**
 * @type {string} The current game version being used, used to navigate to correct folder of items
 */
const gameVersion = `{{ page.version }}`;

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
    if (extension == 'png' || extension == 'jpg' || extension=='svg') dir = 'images';
    else dir = extension;
    return `{{ site.baseurl }}/assets/${dir}/${path}.${extension}`;
}

/**
 * Returns an html element for displaying the icon with the given `name`
 * @param {string} name File name for the svg to use, stored in assets/images/icons
 * @param {string[]} classes Any class names to pass to the svg element
 * @returns {string} The html result
 */
function icon (name, classes=[]) {
    return `<svg class="feather ${classes.join(' ')}">
        <use href="${url_to('feather-sprite', 'svg')}#${name}"/>
    </svg>`;
}

/**
 * Returns the html for an `img` with the given properties
 * @param {string} src The path to image, relative to `assets/{ext}`. Without the extention
 * @param {string} alt The alt text for the image, for text navigators
 * @param {string} title Small text box to show when hovering over the image, defaults to nothing
 * @param {string[]} classes An array of strings, each string is the name of an html `class` the img should have
 * @param {Object.<string,string>} styles A dictionary of html `styles` properties to add. ex: 'width': '64px'
 * @returns 
 */
function html_image (src, alt, title="", classes=[], styles={}) {
    let properties = {"src": url_to(src, 'png'), "alt": alt};
    if (title != "") properties["title"] = title;
    if (classes != []) properties["class"] = classes.join(' ');
    if (styles != {}) properties["style"] = Object.entries(styles).map(([k,v])=>`${k}:${v}`).join(';');
    return `<img ${Object.entries(properties).map(([k,v])=>`${k}="${v}"`).join(' ')}/>`;
}
