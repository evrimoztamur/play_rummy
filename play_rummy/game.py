from enum import Enum
import random
import sys


def eprint(message):
    print(f"\x1b[1;31m{message}\x1b[0m", file=sys.stderr)


def sprint(message):
    print(f"\x1b[1;32m{message}\x1b[0m", file=sys.stderr)


CARD_SUITS = ["♦", "♥", "♣", "♠"]
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

NUM_DECKS = 2

NUM_SUITS = len(CARD_SUITS)
NUM_RANKS = len(CARD_RANKS)
NUM_JOKERS = 3

NUM_SUIT_CARDS = NUM_SUITS * NUM_RANKS
NUM_CARDS_PER_DECK = NUM_SUIT_CARDS + NUM_JOKERS
NUM_CARDS = NUM_DECKS * NUM_CARDS_PER_DECK


class MeldData:
    pass


class SetData(MeldData):
    def __init__(self, cards) -> None:
        self.cards = cards
        self.score = Card.regulars_of(cards)[0].score * len(cards)

    def __str__(self) -> str:
        return f"<Set ${self.score} {self.cards}>"

    def __repr__(self) -> str:
        return str(self)


class RunData(MeldData):
    def __init__(self, cards, equivalent_run) -> None:
        self.cards = cards
        self.equivalent_run = equivalent_run

        self.score = Game.score_cards(equivalent_run)
        self.score += -10 if self.equivalent_run[0].is_ace else 0

    def __str__(self) -> str:
        return f"<Run ${self.score} {self.cards}>"

    def __repr__(self) -> str:
        return str(self)


class InvalidMeld(Exception):
    pass


class IllegalAction(Exception):
    pass


class Card:
    def __init__(self, card_id) -> None:
        self.card_id = card_id

        deck_index = card_id % NUM_CARDS_PER_DECK

        if deck_index >= NUM_SUIT_CARDS:
            self.suit = NUM_SUITS
            self.rank = deck_index % NUM_RANKS - NUM_SUIT_CARDS
        else:
            self.suit = deck_index // NUM_RANKS
            self.rank = deck_index % NUM_RANKS

    @staticmethod
    def from_suit_rank(suit, rank):
        rank = (rank + NUM_RANKS) % NUM_RANKS
        return Card(suit * NUM_RANKS + rank)

    @staticmethod
    def reverse_notation(notation):
        if notation == "J.":
            return Card(NUM_SUIT_CARDS)
        else:
            return Card.from_suit_rank(
                CARD_SUITS.index(notation[0]), CARD_RANKS.index(notation[1:])
            )

    @staticmethod
    def from_test_notation(test_notation):
        return [Card.reverse_notation(n.strip()) for n in test_notation.split(",")]

    @property
    def is_common(self):
        return not (self.is_joker or self.is_ace)

    @property
    def is_joker(self):
        return self.suit == NUM_SUITS

    @property
    def is_ace(self):
        return self.rank == NUM_RANKS - 1

    @property
    def is_court(self):
        return self.rank == 9 or self.rank == 10 or self.rank == 11

    def name(self, *, pad=1):
        if self.is_joker:
            return " J ".ljust(pad).rjust(pad)
        else:
            return f"{CARD_SUITS[self.suit]}{CARD_RANKS[self.rank]: >{pad}}"

    @property
    def score(self):
        if self.is_joker:
            return 20
        elif self.is_ace:
            return 11
        elif self.is_court:
            return 10
        else:
            return self.rank + 2

    @property
    def index(self):
        return self.suit * NUM_SUIT_CARDS + self.rank

    @staticmethod
    def regulars_of(cards):
        return [card for card in cards if not card.is_joker]

    @staticmethod
    def jokers_of(cards):
        return [card for card in cards if card.is_joker]

    @staticmethod
    def commons_of(cards):
        return [card for card in cards if card.is_common]

    @staticmethod
    def first_ace(cards):
        return next((card for card in cards if card.is_ace), None)

    @staticmethod
    def sort_by_rank(cards):
        return sorted(cards, key=lambda c: c.rank)

    @staticmethod
    def are_suits_matching(cards):
        return not (all([card.suit == cards[0].suit for card in cards]))

    @staticmethod
    def are_ranks_matching(cards):
        return not (all([card.rank == cards[0].rank for card in cards]))

    @staticmethod
    def has_duplicates(cards):
        return len(set(cards)) != len(cards)

    def __str__(self) -> str:
        return self.name()

    def __repr__(self) -> str:
        return str(self)

    def pretty(self) -> str:
        if self.suit == 0 or self.suit == 1:
            return f"\x1b[107m\x1b[38;5;196m {self.name(pad=2)} \x1b[0m"
        elif not self.is_joker:
            return f"\x1b[107m\x1b[38;5;16m {self.name(pad=2)} \x1b[0m"
        else:
            return f"\x1b[45m {self.name(pad=2)} \x1b[0m"

    @staticmethod
    def print_cards(cards):
        for i, card in enumerate(cards):
            if (i + 1) % 4 == 0 or i == len(cards) - 1:
                print(f"{i: >2} {card.pretty()}")
            else:
                print(f"{i: >2} {card.pretty()}  ", end="")

    def __hash__(self):
        return hash((self.suit, self.rank))

    def __eq__(self, other):
        if isinstance(other, Card):
            return (
                not (self.is_joker and other.is_joker)
                and self.__hash__() == other.__hash__()
            )
        return NotImplemented


class ActionSort(Enum):
    MELD = 1
    PICK_UP = 2
    DISCARD = 3


class Action:
    def validate(self, game):
        return NotImplemented

    def __repr__(self) -> str:
        return str(self)


class PickUpTarget(Enum):
    DECK = 0
    DISCARD = 1


class PickUpAction(Action):
    def __init__(self, target: PickUpTarget) -> None:
        self.target = target

    def validate(self, game):
        turn = game.turns[-1]

        if Game.turn_contains(turn, PickUpAction):
            raise IllegalAction("already picked up")
        elif self.target not in [PickUpTarget.DECK, PickUpTarget.DISCARD]:
            raise IllegalAction("invalid pick up target")
        elif self.target == PickUpTarget.DISCARD and len(game.turns) <= 1:
            raise IllegalAction("cannot pick up from discard pile on first turn")

    def execute(self, game):
        self.validate(game)

        if self.target == PickUpTarget.DECK:
            card = game.draw_card()
        elif self.target == PickUpTarget.DISCARD:
            card = game.draw_discard()

        game.hands[game.mover].append(card)

    def __str__(self) -> str:
        return f"<Action Pick-up {self.target.name}>"


class MeldAction(Action):
    def __init__(self, card_indices) -> None:
        self.card_indices = card_indices

    def __str__(self) -> str:
        return f"<Action Meld {self.card_indices}>"

    def validate(self, game):
        meld = [game.hands[game.mover][i] for i in self.card_indices]

        self.meld_data = None

        try:
            self.meld_data = Game.validate_set(meld)
        except InvalidMeld:
            pass

        try:
            runs = Game.discover_runs(meld)

            if len(runs) > 1:
                self.meld_data = max(*runs, key=lambda meld: meld.score)
            else:
                self.meld_data = runs[0]
        except InvalidMeld:
            pass

        if not self.meld_data:
            raise IllegalAction("no valid meld for selected cards")

        has_melds = len(game.melds[game.mover]) > 0
        meld_above_threshold = self.meld_data.score >= Game.MELD_THRESHOLD

        if self.meld_data and not has_melds and not meld_above_threshold:
            raise IllegalAction(
                f"first meld score not high enough (${self.meld_data.score} < ${Game.MELD_THRESHOLD}"
            )

    def execute(self, game):
        self.validate(game)

        game.hands[game.mover] = [
            card
            for i, card in enumerate(game.hands[game.mover])
            if i not in self.card_indices
        ]

        game.melds[game.mover].append(self.meld_data)


class DiscardAction(Action):
    def __init__(self, card_index) -> None:
        self.card_index = card_index

    def __str__(self) -> str:
        return f"<Action Discard {self.card_index}>"

    def validate(self, game):
        turn = game.turns[-1]

        if not Game.turn_contains(turn, PickUpAction):
            raise IllegalAction("did not pick up a card")

        if self.card_index >= len(game.hands[game.mover]):
            raise IllegalAction("card index out of range")

    def execute(self, game):
        self.validate(game)

        discarded_card = game.hands[game.mover].pop(self.card_index)

        game.discard_pile.append(discarded_card)


class Game:
    MELD_THRESHOLD = 40

    def __init__(self, num_players) -> None:
        self.cards = [Card(card_id) for card_id in range(NUM_CARDS)]
        self.hands = [[] for _ in range(num_players)]
        self.melds = [[] for _ in range(num_players)]
        self.discard_pile = []
        self.turns = [[]]

    @property
    def mover(self):
        return (len(self.turns) - 1) % len(self.hands)

    def shuffle_cards(self):
        random.shuffle(self.cards)

    def draw_card(self) -> Card:
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            raise IllegalAction("no card available in deck")

    def draw_many(self, num_cards):
        return [self.draw_card() for _ in range(num_cards)]

    def draw_discard(self) -> Card:
        if len(self.discard_pile) > 0:
            return self.discard_pile.pop()
        else:
            raise IllegalAction("no card available in discard pile")

    def start_game(self):
        self.shuffle_cards()

        for hand in self.hands:
            hand.extend(self.draw_many(13))
            hand.sort(key=lambda c: c.index)

            Card.print_cards(hand)

    @staticmethod
    def turn_contains(turn: list[Action], sort):
        return bool(
            next((action for action in turn if isinstance(action, sort)), False)
        )

    def make_action(self, action: Action):
        action.execute(self)

        self.turns[-1].append(action)

        if isinstance(self.turns[-1][-1], DiscardAction):
            self.turns.append([])

        if not self.hands[self.mover]:
            self.end_game()

    def end_game(self):
        sprint("Game over")

        for player, hand in enumerate(self.hands):
            score = Game.score_cards(hand)
            tournament_score = Game.tournament_score(score, len(self.melds[player]) > 0)
            print(f"{player}  {score: >4}  {tournament_score: >3}")

    @staticmethod
    def tournament_score(score, opened):
        if score == 0:
            return 5
        else:
            if opened:
                if score <= 10:
                    return 3
                elif score <= 30:
                    return 2
                else:
                    return 1
            else:
                if score <= 100:
                    return 0
                else:
                    return -1

    @staticmethod
    def score_cards(cards):
        return sum([card.score for card in cards])

    @staticmethod
    def validate_set(cards):
        if Card.has_duplicates(cards):
            raise InvalidMeld("duplicate cards")

        if len(cards) < 3 or len(cards) > 4:
            raise InvalidMeld(f"not of length 3 or 4 ({len(cards)})")

        regulars = Card.regulars_of(cards)

        if len(regulars) < 2:
            raise InvalidMeld("too many jokers")

        if Card.are_ranks_matching(regulars):
            raise InvalidMeld("mismatching ranks")

        return SetData(cards)

    @staticmethod
    def validate_run(cards, jokers):
        suit = cards[0].suit
        run = [cards.pop(0)]

        for card in cards:
            if run[-1].is_joker:
                rank_change = 1
            else:
                rank_change = card.rank - run[-1].rank

            if rank_change > 1:
                if len(jokers) >= rank_change - 1:
                    run.extend(jokers[: rank_change - 1])
                    jokers = jokers[rank_change - 1 :]
                else:
                    return None
            elif not (rank_change == 1 or rank_change == -NUM_RANKS + 1):
                return None

            run.append(card)

        min_rank = run[0].rank
        max_rank = run[-1].rank

        if run[0].is_ace:
            min_rank = -1

        right_waterfall = jokers[: min(len(jokers), NUM_RANKS - max_rank - 1)]
        jokers = jokers[len(right_waterfall) :]
        left_waterfall = jokers[: min(len(jokers), min_rank + 1)]

        equivalent_run = [
            Card.from_suit_rank(suit, rank)
            for rank in range(
                min_rank - len(left_waterfall), max_rank + len(right_waterfall) + 1
            )
        ]

        run = [*left_waterfall, *run, *right_waterfall]

        return RunData(run, equivalent_run)

    @staticmethod
    def discover_runs(cards):
        if Card.has_duplicates(cards):
            raise InvalidMeld("duplicate cards")

        if len(cards) < 3 or len(cards) > NUM_RANKS:
            raise InvalidMeld(f"not of length 3 to {NUM_RANKS} ({len(cards)})")

        regulars = Card.regulars_of(cards)
        commons = Card.commons_of(cards)
        jokers = Card.jokers_of(cards)

        if len(jokers) > len(commons):
            raise InvalidMeld("too few regular cards")

        if Card.are_suits_matching(regulars):
            raise InvalidMeld("mismatching suits in regulars")

        sorted_commons = Card.sort_by_rank(commons)

        ace = Card.first_ace(cards)

        if not ace:
            runs = [sorted_commons]
        else:
            runs = [[ace, *sorted_commons], [*sorted_commons, ace]]

        runs = [Game.validate_run(run, jokers.copy()) for run in runs]
        runs = [run for run in runs if run]

        if not runs:
            raise InvalidMeld("no valid run possible")

        return runs
