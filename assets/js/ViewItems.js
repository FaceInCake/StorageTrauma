---
---

function viewItem (id) {
    window.location = `{{site.baseurl}}/Item.html?id=${id}`;
}


let yes = () => '<i class="fa-solid fa-check" style="color: #1aea59;">Yes</i>';
let no = () => '<i class="fa-solid fa-xmark" style="color: #eb250f;">No</i>';
let NA = () => '<span style="color: grey">N/A</span>'

$(async function main () {
    $('#AllItems').DataTable({
        ajax: {
            url: "{{site.baseurl}}/assets/json/{{ page.version }}/ViewItemsList.json",
            dataSrc: ''
        },
        columns: [
            {   data: 0, // id
                title: 'ID',
                render: function (data, type, row) {
                    return `<a href=\"{{site.baseurl}}/Item.html?id=${data}\">${data}</a>`
                }
            },
            {   data: 1, // name
                title: 'Name'
            },
            {   data: 2, // price
                title: 'Price',
                render: function (data, type, row) {
                    if (type == 'display') {
                        if (data=="") return NA();
                        return DataTable.render.number("'",null,0,null,' mk').display(data);
                    }
                    return data;
                }
            },
            {   data: 3, // craftable
                title: 'Craftable',
                render: function (data, type, row) {
                    if (data==1) return yes();
                    return no();
                }
            },
            {   data: 4, // decon-able
                title: 'Deconstructable',
                render: function (data, type, row) {
                    if (data==1) return yes();
                    return no();
                }
            },
        ]
    });
});
