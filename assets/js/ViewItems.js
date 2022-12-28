
function viewItem (id) {
    window.location = `./Item.html?id=${id}`;
}

$.getJSON(
    "./assets/json/Items/"+VERSION+"/!ItemList.json",
    data => Array.from(data).map(val => {
        td = $("#item-data")
        $.getJSON(`./assets/json/Items/${VERSION}/${val}.json`, item => {
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