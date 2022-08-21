
const fetchJson = async (name) => {
    try {
        data = await fetch("./assets/json/"+name+".json");
        response = await data.json();
        return response;
    } catch (error) {
        console.error(error);
    }
};

// fetchJson("Items")
// .then(data => {
//     for (const [k,v] of Object.entries(data)) {
//         console.log(k, v);
//     }
// });
