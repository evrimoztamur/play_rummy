from base64 import b32encode
from os import urandom
from time import time

from flask import Flask, flash, redirect, render_template, request, url_for
from play_rummy.exceptions import IllegalAction, InvalidMeld, InvalidQuery

from play_rummy.game import (
    Card,
    DiscardAction,
    Game,
    MeldAction,
    PickUpAction,
    PickUpTarget,
    SwapAction,
)

app = Flask(__name__)
app.secret_key = "1"


def make_token(nbytes=4):
    tok = urandom(nbytes)
    timestamp = int(time()).to_bytes(4, byteorder="big")

    return b32encode(timestamp + tok).rstrip(b"=").decode("ascii").lower()


@app.errorhandler(InvalidQuery)
def handle_invalid_query(e):
    flash(str(e), "error")
    return redirect(request.referrer)


@app.errorhandler(IllegalAction)
def handle_illegal_action(e):
    flash(str(e), "error")
    return redirect(request.referrer)


@app.errorhandler(InvalidMeld)
def handle_illegal_action(e):
    flash(str(e), "error")
    return redirect(request.referrer)


class Player:
    def __init__(self, index) -> None:
        self.index = index
        self.ready = False

    @property
    def number(self):
        return self.index + 1


class Lobby:
    def __init__(self, game) -> None:
        self.game = game
        self.players = {}
        self.player_slots = list(range(self.max_players))
        self.ticks = 0

    @property
    def max_players(self):
        return len(self.game.hands)

    @property
    def all_players_ready(self):
        return len(self.players) == self.max_players and all(
            player.ready for player in self.players.values()
        )

    def tick(self):
        self.ticks += 1

    def hand_for(self, session_id):
        player = self.players.get(session_id)

        if player:
            return self.game.hands[player.index]
        else:
            raise InvalidQuery("player not in lobby")

    def join_player(self, session_id) -> str:
        player = self.players.get(session_id)

        if self.game.started or self.game.ended:
            raise InvalidQuery("cannot join an active game")

        if player:
            raise InvalidQuery("already in lobby")
        else:
            self.tick()

            self.players[session_id] = Player(self.player_slots.pop(0))
            return session_id

    def ready_player(self, session_id):
        player = self.players.get(session_id)

        if self.game.started or self.game.ended:
            raise InvalidQuery("cannot ready for an active game")

        if player:
            self.tick()

            player.ready = True

            if self.all_players_ready:
                self.game.start_game()
        else:
            raise InvalidQuery("cannot ready a player which is not in lobby")

    def leave_player(self, session_id):
        player = self.players.get(session_id)

        if self.game.ended:
            raise InvalidQuery("cannot leave a finished game")

        if player:
            self.tick()

            self.player_slots.append(self.players[session_id].index)
            del self.players[session_id]

            if self.game.started:
                self.game.end_game()
        else:
            raise InvalidQuery("player not in lobby")

    @staticmethod
    def selected_cards(form):
        return [Card(int(card_id)) for card_id in form.getlist("selected_card_id")]

    def interpret_action(self, form):
        action_sort = form.get("action_sort")

        action_sorts = {"pick_up", "meld", "discard", "swap"}
        pick_up_targets = {"deck": PickUpTarget.DECK, "discard": PickUpTarget.DISCARD}

        if action_sort in action_sorts:
            if action_sort == "pick_up":
                action_target = pick_up_targets.get(form.get("action_target"))

                if action_target is not None:
                    return PickUpAction(action_target)
                else:
                    raise InvalidQuery(
                        "pick-up action target is not provided or unknown"
                    )
            elif action_sort == "meld":
                cards = Lobby.selected_cards(form)

                if len(cards) > 0:
                    return MeldAction(cards)
                else:
                    raise InvalidQuery("must select cards for a meld")
            elif action_sort == "discard":
                cards = Lobby.selected_cards(form)

                if len(cards) == 1:
                    return DiscardAction(cards[0])
                elif len(cards) == 0:
                    raise InvalidQuery("must select a card to discard")
                else:
                    raise InvalidQuery("can only discard one card per turn")
            elif action_sort == "swap":
                cards = Lobby.selected_cards(form)

                if len(cards) > 0:
                    return SwapAction(cards)
                else:
                    raise InvalidQuery("must select cards to swap")
        else:
            raise InvalidQuery("action sort is not provided or unknown")

    def act_player(self, session_id, form):
        player = self.players.get(session_id)

        if player and self.game.started:
            if player.index == self.game.mover:
                action = self.interpret_action(form)

                self.game.make_action(action)
            else:
                raise InvalidQuery("not your turn")
        else:
            raise InvalidQuery("cannot ready a player which is not in lobby")


lobbies = {}


def identify_player():
    session_id = request.cookies.get("session_id")

    if session_id:
        return (True, session_id)
    else:
        return (False, make_token())


@app.get("/")
def get_index():
    _, session_id = identify_player()

    return render_template("lobbies.html", lobbies=lobbies, session_id=session_id)


@app.get("/lobby/create")
def get_lobby_create():
    return render_template("lobby_create.html")


@app.post("/lobby/create")
def post_lobby_create():
    num_players = request.form.get("num_players")
    meld_threshold = request.form.get("meld_threshold")

    if num_players and meld_threshold:
        lobby_id = make_token()
        lobbies[lobby_id] = Lobby(Game(int(num_players), int(meld_threshold)))

        return post_lobby_join(lobby_id)
    else:
        raise InvalidQuery("did not include number of players or meld threshold")


@app.get("/lobby/<lobby_id>")
def get_lobby(lobby_id):
    lobby: Lobby = lobbies.get(lobby_id)
    _, session_id = identify_player()

    if lobby is not None:
        context = {
            "lobby_id": lobby_id,
            "lobby": lobby,
            "session_id": session_id,
        }

        if lobby.game.started:
            return render_template("lobby_started.html", **context)
        elif lobby.game.ended:
            return render_template("lobby_ended.html", **context)
        else:
            return render_template("lobby_prepared.html", **context)
    else:
        raise InvalidQuery("lobby not available")


@app.post("/lobby/<lobby_id>/join")
def post_lobby_join(lobby_id):
    lobby: Lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None:
        if len(lobby.players) < lobby.max_players:
            session_id = lobby.join_player(session_id)
            response = redirect(url_for("get_lobby", lobby_id=lobby_id))
            if not session_found:
                response.set_cookie("session_id", session_id)
            return response
        else:
            raise InvalidQuery("lobby is full")
    else:
        raise InvalidQuery("lobby not available")


@app.post("/lobby/<lobby_id>/leave")
def post_lobby_leave(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None and session_found:
        lobby.leave_player(session_id)

        if len(lobby.players) == 0:
            del lobbies[lobby_id]

            return redirect(url_for("get_index"))
        else:
            return redirect(url_for("get_lobby", lobby_id=lobby_id))
    else:
        raise InvalidQuery("lobby not available")


@app.post("/lobby/<lobby_id>/ready")
def post_lobby_ready(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None and session_found:
        lobby.ready_player(session_id)

        return redirect(url_for("get_lobby", lobby_id=lobby_id))
    else:
        raise InvalidQuery("lobby not available")


@app.post("/lobby/<lobby_id>/act")
def post_lobby_act(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None and session_found:
        lobby.act_player(session_id, request.form)

        return redirect(url_for("get_lobby", lobby_id=lobby_id))
    else:
        raise InvalidQuery("lobby not available")


@app.get("/lobby/<lobby_id>/state")
def get_lobby_state(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, _ = identify_player()

    if lobby is not None and session_found:
        return {"ticks": lobby.ticks}
    else:
        raise InvalidQuery("lobby not available")


@app.get("/lobby/<lobby_id>/game_state")
def get_lobby_game_state(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, _ = identify_player()

    if lobby is not None and session_found:
        return {"num_actions": lobby.game.num_actions, "state": lobby.game.state}
    else:
        raise InvalidQuery("lobby not available")


@app.context_processor
def svg_icon_processor():
    def svg_icon(icon_name, *args, viewbox="0 0 40 48"):
        class_list = " ".join(
            [
                "icon-{}".format(arg)
                for arg in [icon_name, *(args if args is not None else [])]
            ]
        )
        svg_tag = '<svg viewbox="{viewbox}" class="{class_list}"><use href="#{icon_name}"></use></svg>'.format(
            viewbox=viewbox, icon_name=icon_name, class_list=class_list
        )

        return svg_tag

    return dict(svg_icon=svg_icon)
