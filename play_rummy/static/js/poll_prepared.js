let ticks = document.getElementById("ticks").value | 0;;
let gsqu = document.getElementById("state_query_uri").value;

let timer = setInterval(() => {
    fetch(gsqu)
        .then((response) => response.json())
        .then((data) => compareState(data));
}, 1000);

function compareState(state) {
    if (state.ticks != ticks) {
        location.reload();
    }
}