
function viewItem (id) {
    window.location = `Item.html?id=${id}`;
}

$.getJSON(
    "../assets/json/Items.json",
    data => $("#item-data").html(Object.entries(data).map(val =>
        `<tr onclick="viewItem('${val[0]}');">
        <td>${val[1].name}</td>
        <td href="Item.html?id=${val[0]}">${val[1].prices.default}</td>
        <td><i class="fa-solid fa-${val[1].recipes.length>0?"check":"close"}"></i></td>
        <td><i class="fa-solid fa-${Object.keys(val[1].deconsTo).length>0?"check":"close"}"></i></td>
        </tr>`
    ))
);