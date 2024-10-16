---
---

function alertError (msg) {
    alert(msg);
    history.back();
}

// Capitalizes first letter, nothing else
function quickTitleCase (str) {
    return str.charAt(0).toUpperCase() + str.substring(1).toLowerCase();
}

$(async function main () {
    const params = new Proxy(new URLSearchParams(window.location.search), {get:(s,p)=>s.get(p)});
    let id = params.id;
    let url = `{{site.baseurl}}/assets/json/items/{{page.version}}/${id}.json`;
    const item = await $.getJSON(url).fail(() => alertError(`Failed to find the given item: '${id}'`));
    let iconUrl = `{{site.baseurl}}/assets/images/items/{{page.version}}/icons/${id}.png`;
    $("#item-icon").html(`<img src="${iconUrl}" alt="item icon">`);
    let spriteUrl =`{{site.baseurl}}/assets/images/items/{{page.version}}/sprites/${id}.png`;
    $("#item-sprite").html(`<img src="${spriteUrl}" alt="item sprite">`);
    $("#item-name").html(item.name);
    $("#item-categories").html("- "+item.category.split(",").join(" - ")+" -");
    $("#item-desc").html(item.desc);
    $("#item-tags").html(item.tags.join(", "));
    for (let k in item.prices) {
        $("#prices-header").append(`<th>${quickTitleCase(k)}</th>`);
        let p = item.prices[k];
        if (p) p += " mk"; else p = "∅";
        $("#prices-body").append(`<td>${p}</td>`)
    }

});
