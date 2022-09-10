from base64 import b32encode
from os import urandom
import random
from time import time
from flask import Flask, redirect, url_for, render_template, request
from play_rummy.game import (
    Action,
    DiscardAction,
    Game,
    MeldAction,
    PickUpAction,
    PickUpTarget,
)
from tests.replays import TEST_REPLAYS

app = Flask(__name__)


def make_token(nbytes=4):
    tok = urandom(nbytes)
    timestamp = int(time()).to_bytes(4, byteorder="big")

    return b32encode(timestamp + tok).rstrip(b"=").decode("ascii").lower()


class InvalidQuery(Exception):
    pass


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

    @property
    def max_players(self):
        return len(self.game.hands)

    def hand_for(self, session_id):
        player = self.players.get(session_id)

        if player:
            return self.game.hands[player.index]
        else:
            raise InvalidQuery("player not in lobby")

    def join_player(self, session_id) -> str:
        player = self.players.get(session_id)

        if player:
            raise InvalidQuery("already in lobby")
        else:
            self.players[session_id] = Player(self.player_slots.pop(0))
            return session_id

    def leave_player(self, session_id):
        player = self.players.get(session_id)

        if player:
            self.player_slots.append(self.players[session_id].index)
            del self.players[session_id]

            if self.game.started:
                self.game.end_game()
        else:
            raise InvalidQuery("player not in lobby")

    @property
    def all_players_ready(self):
        return len(self.players) == self.max_players and all(
            player.ready for player in self.players.values()
        )

    def ready_player(self, session_id):
        player = self.players.get(session_id)

        if player:
            player.ready = True

            if self.all_players_ready:
                self.game.start_game()
        else:
            raise InvalidQuery("cannot ready a player which is not in lobby")

    def index_selected_cards_in_hand(self, form):
        hand = [card.card_id for card in self.game.hands[self.game.mover]]
        card_ids = [int(card_id) for card_id in form.getlist("selected_card_id")]

        print(hand, card_ids)

        if set(card_ids) <= set(hand):
            return [hand.index(card_id) for card_id in card_ids]
        else:
            raise InvalidQuery("hand does not contain all selected cards")

    def interpret_action(self, form):
        action_sort = form.get("action_sort")

        action_sorts = {"pick_up", "meld", "discard"}
        pick_up_targets = {"deck": PickUpTarget.DECK, "discard": PickUpTarget.DISCARD}

        if action_sort in action_sorts:
            if action_sort == "pick_up":
                action_target = pick_up_targets.get(form.get("action_target"))

                if action_target is not None:
                    return PickUpAction(action_target)
                else:
                    return InvalidQuery(
                        "pick-up action target is not provided or unknown"
                    )
            elif action_sort == "meld":
                card_indices = self.index_selected_cards_in_hand(form)

                if len(card_indices) > 0:
                    return MeldAction(card_indices)
                else:
                    return InvalidQuery("must select cards for a meld")
            elif action_sort == "discard":
                card_indices = self.index_selected_cards_in_hand(form)

                if len(card_indices) == 1:
                    return DiscardAction(card_indices[0])
                else:
                    return InvalidQuery("can only discard one card per turn")
        else:
            return InvalidQuery("action sort is not provided or unknown")

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


@app.post("/lobby/create")
def post_lobby_create():
    lobby_id = make_token()
    lobbies[lobby_id] = Lobby(Game(2))

    return post_lobby_join(lobby_id)


@app.post("/lobby/create/test")
def post_lobby_create_test():
    lobby_id = make_token()

    random.seed(1)

    game = Game(4)
    game.start_game()

    for action in TEST_REPLAYS[0][2][:-10]:
        try:
            game.make_action(action)
        except:
            pass

    lobbies[lobby_id] = Lobby(game)

    lobbies[lobby_id].join_player("a")
    lobbies[lobby_id].join_player("b")
    lobbies[lobby_id].join_player("c")

    return post_lobby_join(lobby_id)


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
        return "<p>Lobby not found</p>"


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
            return "<p>Lobby is full!</p>"
    else:
        return "<p>Lobby not found!</p>"


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
        return "<p>Lobby not found</p>"


@app.post("/lobby/<lobby_id>/ready")
def post_lobby_ready(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None and session_found:
        lobby.ready_player(session_id)

        return redirect(url_for("get_lobby", lobby_id=lobby_id))
    else:
        return "<p>Lobby not found</p>"


@app.post("/lobby/<lobby_id>/act")
def post_lobby_act(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, session_id = identify_player()

    if lobby is not None and session_found:
        lobby.act_player(session_id, request.form)

        return redirect(url_for("get_lobby", lobby_id=lobby_id))
    else:
        return "<p>Lobby not found</p>"


@app.get("/lobby/<lobby_id>/game_state")
def get_lobby_game_state(lobby_id):
    lobby = lobbies.get(lobby_id)
    session_found, _ = identify_player()

    if lobby is not None and session_found:
        return {
            "num_actions": lobby.game.num_actions,
            "state": lobby.game.state
        }
    else:
        return "<p>Lobby not found</p>"


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
