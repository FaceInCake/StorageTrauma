---
---

// Create search index
var index = elasticlunr(function(){
    this.addField("id");
    this.setRef("id");
    this.addField("name");
    this.addField("desc");
    this.addField("category");
    this.addField("tags");
    this.addField("deconsTo");
    this.addField("recipes");
    this.addField("price");
    this.saveDocument(true);
});

var lastBg = "warning";
function updateProgressBar(percentile, bg, text) {
    $("#progress").attr("aria-valuenow", `${percentile}`);
    $("#progressbar")
        .removeClass(`bg-${lastBg}`).addClass(`bg-${bg}`)
        .css("width", `${percentile}%`).html(`${text}...`)
    ;
    lastBg = bg;
}

function viewItem (id) {
    window.location = `{{site.baseurl}}/Item.html?id=${id}`;
}

function card (item) {
    let imageUrl = `{{site.baseurl}}/assets/images/items/{{page.version}}/icons/${item.id}.png`;
    let price = !!item.price? item.price+" mk" : "∅";
    let con = !!item.recipes? 'success' : 'danger';
    let dec = !!item.deconsTo? 'success' : 'danger';
    return `
    <a class="card" href="{{site.baseurl}}/Item.html?id=${item.id}">
        <text>${item.name}</text>
        <div>
            <div class="item-icon">
                <img alt="MyItem" src="${imageUrl}">
            </div>
            <div class="icons">
                <i class="fas fa-hammer text-${con}" aria-hidden="true">C</i>
                <i class="fas fa-cogs text-${dec}" aria-hidden="true">D</i>
            </div>
            <div>${price}</div>
        </div>
    </div>`
}

function onError (args) {
    alert("Failed to search: ("+args+")");
    history.back();
}

$(async function main () {
    // Populate search index
    updateProgressBar(20, 'info', 'Fetching');
    let docUrl = "{{site.baseurl}}/assets/json/{{ page.version }}/SearchDoc.json";
    let searchDoc = await $.getJSON(docUrl);
    searchDoc.forEach(elm => index.addDoc(elm)); // console.log(elm)
    // Execute search
    updateProgressBar(50, 'success', 'Searching');
    const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    const results = await index.search(params.search, {
        fields: {
            name: {boost: 1.5},
            id: {boost: 1.1},
            category: {boost: 1},
            tags: {boost: 1},
            desc: {boost: 0.4},
            recipes: {boost: 0.4},
            deconsTo: {boost: 0.4},
            price: {boost: 0.3}
        },
        expand: true
    });
    if (results.length == 0) {
        $(".loader").html("No results found :(");
        return;
    }
    // Populate table
    updateProgressBar(90, 'info', 'Populating');
    let imagePromises = [];
    results.forEach(elm => {
        $('.search-grid').append(card(elm.doc));
        imagePromises.push(new Promise(res => {
            $(".search-grid:last-child img").on("load", res);
        }));
    });
    await Promise.all(imagePromises);
    // Finish displaying
    updateProgressBar(100, 'success', 'Displaying');
    $(".loader").slideUp(1000);
});
