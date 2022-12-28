---
---

function viewItem (id) {
    window.location = `{{site.baseurl}}/Item.html?id=${id}`;
}

$.getJSON(
    "{{site.baseurl}}/assets/json/Items/{{ page.version }}/!ItemList.json",
    data => Array.from(data).map(val => {
        td = $("#item-data")
        $.getJSON(`{{site.baseurl}}/assets/json/Items/{{ page.version }}/${val}.json`, item => {
            td.append(
                // <th>Name</th>
                // <th>Base Price</th>
                // <th>Craftable</th>
                // <th>Can Decon</th>    
                `<tr>
                    <td>${item.name}</td>
                    <td>${item.prices.default}</td>
                    <td>${item.recipes.length>0 ? 'Y' : 'N'}</td>
                    <td>${item.deconsTo.length>0 ? 'Y' : 'N'}</td>
                </tr>`
            );
        })
    }
));