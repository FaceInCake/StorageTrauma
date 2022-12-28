
$.getJSON(
    "/assets/json/Items.json",
    data => {
        const params = new Proxy(new URLSearchParams(window.location.search), {
            get: (searchParams, prop) => searchParams.get(prop),
        });
        var item = data[params.id];

        // $("#item-icon").html(`<img src="assets/images/ItemIcons/${params.id}.png" alt="Item Icon" width="32" height="32"/>`)
        $("#item-icon img").attr("src",`/assets/images/ItemIcons/${params.id}.png`);
        $("#item-icon img").ready(
            () => {
                $("#item-icon span").hide();
                $("#item-icon img").removeClass("invisible");
            }
        );
        
        $("#item-name").html(item.name);
        
        var bp = item.prices.default;
        $("#p-base").html(bp);
        $("#p-outpost").html(item.prices.outpost ?? bp);
        $("#p-city").html(item.prices.city ?? bp);
        $("#p-medical").html(item.prices.medical ?? bp);
        $("#p-engineering").html(item.prices.engineering ?? bp);
        $("#p-armory").html(item.prices.armory ?? bp);
        $("#p-research").html(item.prices.research ?? bp);
        $("#p-military").html(item.prices.military ?? bp);
        $("#p-mine").html(item.prices.mine ?? bp);
        
        var ba = item.available.default;
        $("#a-base").html(ba);
        $("#a-outpost").html(item.available.outpost ?? ba);
        $("#a-city").html(item.available.city ?? ba);
        $("#a-medical").html(item.available.medical ?? ba);
        $("#a-engineering").html(item.available.engineering ?? ba);
        $("#a-armory").html(item.available.armory ?? ba);
        $("#a-research").html(item.available.research ?? ba);
        $("#a-military").html(item.available.military ?? ba);
        $("#a-mine").html(item.available.mine ?? ba);

        $("#decons-into").html(
            Object.entries(item.deconsTo).map(elm => (
                `${elm[1]}x ${data[elm[0]].name}`
            )).join("<br>")
        );
        $("#recipes").html("Berp");
    }
);
