let ticks = document.getElementById("ticks").value | 0;;
let gsqu = document.getElementById("state_query_uri").value;

let timer = setInterval(async () => {
    try {
        await fetch(gsqu, { redirect: "error" })
            .then((response) => response.json())
            .then((data) => compareState(data));
    } catch {
        clearInterval(timer);
    }
}, 1000);

function compareState(state) {
    if (state.ticks != ticks) {
        location.reload();
    }
}