import random
import pytest
from play_rummy import __version__

from play_rummy.game import (
    Card,
    Game,
    IllegalAction,
    InvalidMeld,
    eprint,
    sprint,
)

from tests.replays import TEST_REPLAYS
from tests.runs import TEST_RUNS
from tests.sets import TEST_SETS


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.parametrize(["test_set", "valid"], TEST_SETS)
def test_validate_set(test_set, valid):
    meld = Card.from_test_notation(test_set)

    try:
        print(f"\nSet\t{meld}")
        sprint(f"{Game.validate_set(meld)}")

        assert valid
    except InvalidMeld:
        assert not valid


@pytest.mark.parametrize(["test_run", "valid"], TEST_RUNS)
def test_discover_runs(test_run, valid):
    meld = Card.from_test_notation(test_run)

    try:
        print(f"\nRun\t{meld}")
        sprint(f"{Game.discover_runs(meld)}")

        assert valid
    except InvalidMeld:
        assert not valid


@pytest.mark.parametrize(["seed", "num_players", "test_actions"], TEST_REPLAYS)
def test_game_replay(seed, num_players, test_actions):
    random.seed(seed)

    game = Game(num_players)
    game.start_game()

    for action in test_actions:
        try:
            discard_top = game.discard_pile[-1] if game.discard_pile else None

            sprint(f"> {action}")
            print(f"   Deck {len(game.cards)}", end="")
            print(f"   Discard {discard_top} ({len(game.discard_pile)})")

            game.make_action(action)

            Card.print_cards(game.hands[game.mover])
            print()
        except IllegalAction as e:
            eprint(f"Error {e}")
