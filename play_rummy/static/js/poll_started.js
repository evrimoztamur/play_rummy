let numActions = document.getElementById("num_actions").value | 0;;
let state = document.getElementById("game_state").value | 0;
let gsqu = document.getElementById("game_state_query_uri").value;

let timer = setInterval(async () => {
    try {
        await fetch(gsqu, { redirect: "error" })
            .then((response) => response.json())
            .then((data) => compareGameState(data));
    } catch {
        clearInterval(timer);
    }
}, 1000);

function compareGameState(gameState) {
    if (gameState.num_actions != numActions || gameState.state != state) {
        location.reload();
    }
}