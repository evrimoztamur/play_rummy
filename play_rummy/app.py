from base64 import b32encode
from os import urandom
import random
from time import time
from flask import Flask, redirect, url_for, render_template, request
from play_rummy.game import CARD_RANKS, Game

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
        else:
            raise InvalidQuery("player not in lobby")

    def ready_player(self, session_id):
        player = self.players.get(session_id)

        if player:
            player.ready = True
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
    lobbies[lobby_id] = Lobby(Game(4))

    return post_lobby_join(lobby_id)


@app.get("/lobby/<lobby_id>")
def get_lobby(lobby_id):
    lobby: Lobby = lobbies.get(lobby_id)
    _, session_id = identify_player()

    if lobby is not None:
        cards = filter_shuffle(
            [
                (suit, rank)
                for suit in ["diamonds", "hearts", "clubs", "spades"]
                for rank in CARD_RANKS
            ]
        )[:13]
        context = {
            "lobby_id": lobby_id,
            "lobby": lobby,
            "session_id": session_id,
            "cards": cards,
        }

        return render_template("lobby.html", **context)
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


@app.template_filter("shuffle")
def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq
