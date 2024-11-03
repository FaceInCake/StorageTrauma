
// Capitalizes first letter, nothing else
function quickTitleCase (str) {
    return str.charAt(0).toUpperCase() + str.substring(1).toLowerCase();
}

$(async function main() {
    let item_id = URL_params.id;

    $("#item-icon img").attr("src", url_to(`items/${gameVersion}/icons/${item_id}`, 'png'));
    $("#item-icon img").ready(() => {
        $("#item-icon span").hide();
        $("#item-icon img").removeClass("d-none");
    });

    $("#item-sprite img").attr("src", url_to(`items/${gameVersion}/sprites/${item_id}`, 'png'));
    $("#item-sprite img").ready(() => {
        $("#item-sprite span").hide();
        $("#item-sprite img").removeClass("d-none");
    });

    let item = await $.getJSON(url_to(`${gameVersion}/items/${item_id}`, 'json'));

    $("#item-name").html(item.name);
    $("#item-name").attr('title', (t) => `In game ID: ${item_id}`);
    $("#item-categories").html('- ' + item.category.replace(',', ' - ') + ' -');
    $("#item-desc").html(item.desc);
    $("#item-tags").html(item.tags.join(", "));
    
    let pi = new PriceInfo(item.priceInfo);
    if (pi.basePrice) {
        defaultListing.merchants.forEach(merchant => {
            let l = pi[merchant];
            let offered = l.sold || l.minAvailable != 0 || l.maxAvailable != 0;
            let elms = [
                offered
                ?   Math.ceil(pi.getBuyPrice(merchant)).toFixed()
                :   '-',
                Math.ceil(pi.getSellPrice(merchant)).toFixed(),
                offered
                ?   `${l.minAvailable}` + (
                        l.maxAvailable != l.minAvailable
                        ?   `->${l.maxAvailable}` 
                        :   ''
                    )
                :   '-',
                Object.keys(l.repRequired).length
                ?   '<span style="white-space:pre-wrap;">' + Object.entries(l.repRequired)
                    .map(([k,v]) => `${quickTitleCase(k)} = ${v}`)
                    .join('\n') + '</span>'
                :   '-',
                l.minLevelDifficulty || '-',
                l.canBeSpecial
                ?   '<i class="fa-solid fa-check"></i>'
                :   '<i class="fa-solid fa-xmark" style="color: #eb250f;"></i>',
                l.requiresUnlock
                ?   '<i class="fa-solid fa-check text-warning"></i>'
                :   '-'
            ];
        $("#pricing-body").append(`<tr><th>${quickTitleCase(merchant)}</th><td>${elms.join("</td><td>")}</td></tr>`);
        }); // end merchants.forEach
    } else {
        $("#pricing-table").hide();
    }

    if (item.recipes.length) {
        let rows = [];

        let recipeCard = (recipe) => {
            let requiredItems = Object.entries(recipe.required)
                .map(([k,v]) => `${v} x ${k}`)
                .join('\n');
            return `
                <div class="card d-flex flex-row p-2 w-fit">
                    ${
                        Object.keys(recipe.required).length
                        ?   `<div class="p-1" style="white-space:pre-wrap;">${requiredItems}</div>
                            <div class="vr m-1"></div>`
                        :   ''
                    }
                    <div class="flex-column p-1">
                        <div>
                            ${icon('upload')}
                            <span>${recipe.output}x</span>
                        </div>
                        <div>
                            ${icon('clock')}
                            <span>${recipe.time}s</span>
                        </div>
                        <div>
                            ${icon('tool')}
                            <span>${quickTitleCase(recipe.machine)}</span>
                        </div>
                        ${
                            recipe.requiredMoney
                            ?   `<div>${icon('dollar-sign')}<span> ${recipe.requiredMoney}</span></div>`
                            :   ''
                        }
                    </div>
                </div>
            `;
        };
        item.recipes.forEach((recipe) => rows.push(recipeCard(recipe)));
        $("#recipe-body").html(`${rows.join('')}`);
    } else {
        $("#recipe-section").hide();
    }
    

});


// let finalP = get('basePrice') * get('multiplier') * get('buyingPriceModifier');
// elms.push(sold && minAvail!=0 ? `${finalP.toFixed(2)}` : '-');
// elms.push('' + (get('basePrice') * get('multiplier') * 0.3).toFixed(2));
// elms.push(sold||(minAvail==0 && maxAvail==0) ? ('' + minAvail + (maxAvail && maxAvail!=minAvail ? '->' + maxAvail : '')) : '-');
// elms.push(reps.length ? reps.map(([k,v],i,a) => '' + quickTitleCase(k) + ' = ' + v).join('\n') : '-');
// elms.push(minDiff==0 ? '-' : '' + minDiff);
// elms.push(get('canBeSpecial') ? '<i class="fa-solid fa-check"></i>' : '<i class="fa-solid fa-xmark" style="color: #eb250f;"></i>')
// elms.push(get('requiresUnlock') ? '<i class="fa-solid fa-check text-warning"></i>' : '-')



    // const params = new Proxy(new URLSearchParams(window.location.search), {get:(s,p)=>s.get(p)});
    // let id = params.id;
    // let url = `{{site.baseurl}}/assets/json/items/{{page.version}}/${id}.json`;
    // const item = await $.getJSON(url).fail(() => alertError(`Failed to find the given item: '${id}'`));
    // let iconUrl = `{{site.baseurl}}/assets/images/items/{{page.version}}/icons/${id}.png`;
    // $("#item-icon").html(`<img src="${iconUrl}" alt="item icon">`);
    // let spriteUrl =`{{site.baseurl}}/assets/images/items/{{page.version}}/sprites/${id}.png`;
    // $("#item-sprite").html(`<img src="${spriteUrl}" alt="item sprite">`);
    // $("#item-name").html(item.name);
    // $("#item-categories").html("- "+item.category.split(",").join(" - ")+" -");
    // $("#item-desc").html(item.desc);
    // $("#item-tags").html(item.tags.join(", "));
    // for (let k in item.prices) {
    //     $("#prices-header").append(`<th>${quickTitleCase(k)}</th>`);
    //     let p = item.prices[k];
    //     if (p) p += " mk"; else p = "∅";
    //     $("#prices-body").append(`<td>${p}</td>`)
    // }
