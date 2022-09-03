import random
import sys


def eprint(message):
    print(f"\x1b[1;31m{message}\x1b[0m", file=sys.stderr)


def sprint(message):
    print(f"\x1b[1;32m{message}\x1b[0m", file=sys.stderr)


CARD_SUITS = ["♣", "♦", "♥", "♠"]
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
        return f"Set {self.score}* {self.cards}"

    def __repr__(self) -> str:
        return str(self)


class RunData(MeldData):
    def __init__(self, cards, equivalent_run) -> None:
        self.cards = cards
        self.equivalent_run = equivalent_run

        self.score = sum([card.score for card in self.equivalent_run])
        self.score += 10 if self.equivalent_run[-1].is_ace else 0

    def __str__(self) -> str:
        return f"Run {self.score}* {self.cards}"

    def __repr__(self) -> str:
        return str(self)


class InvalidMeld(Exception):
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

    @property
    def name(self):
        if self.is_joker:
            return "J."
        else:
            return f"{CARD_SUITS[self.suit]}{CARD_RANKS[self.rank]}"

    @property
    def score(self):
        if self.is_joker:
            return -1
        elif self.is_ace:
            return 1
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
        return self.name

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self):
        return hash((self.suit, self.rank))

    def __eq__(self, other):
        if isinstance(other, Card):
            return (
                not (self.is_joker and other.is_joker)
                and self.__hash__() == other.__hash__()
            )
        return NotImplemented


class Game:
    def __init__(self, num_players) -> None:
        self.cards = list(range(NUM_CARDS))
        self.players = list(range(num_players))

    def shuffle_cards(self):
        random.shuffle(self.cards)

    def draw_card(self) -> Card:
        return Card(self.cards.pop())

    def draw_many(self, num_cards):
        return [self.draw_card() for _ in range(num_cards)]

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
                    run.extend(jokers[:rank_change])
                    jokers = jokers[rank_change:]
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


test_sets = [
    "♣2, ♦2",
    "♣2, ♦2, ♥2",
    "♣3, ♥3, ♥3",
    "J., J., ♥2",
    "♣2, ♦2, ♥2, J.",
    "♣2, ♦2, J., J.",
    "J., ♦2, J., J.",
    "♥5, ♦5, J., ♠5",
    "♥5, ♦5, J., ♠7",
    "♣2, ♦2, ♥2, J.",
    "♣2, ♦2, ♥2, J., J.",
]

for notation in test_sets:
    meld = Card.from_test_notation(notation)
    print(f"\nSet\t{meld}")

    try:
        sprint(f"{Game.validate_set(meld)}")
    except InvalidMeld as e:
        eprint(f"Error {e}")


test_runs = [
    "♣2, ♦2",
    "♣A, ♦2, ♥3",
    "♣A, ♣2, ♣3",
    "♣A, ♣2, ♣3, ♣3",
    "♣3, ♣4, ♣5, ♣6",
    "♣A, ♣2, ♣3, ♣4, ♣5",
    "♣A, ♣2, ♣3, J., ♣5",
    "♣A, ♣2, ♣3, J., ♣4",
    "♣A, ♣2, ♣3, J., ♣Q",
    "♣A, ♣J, ♣Q, J., ♣K",
    "♣A, ♣10, ♣J, J., ♣Q",
    "♣A, ♣2, J., ♣4, ♣5, J., ♣7, J., J.",
    "♣A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣K, ♣Q, J.",
    "♣A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣K, J.",
    "♣A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣Q, ♣K",
    "J., ♣A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣Q",
    "♥10, J., J., ♥Q",
    "♥10, J., J., J., ♥Q",
    "♥10, J., J., ♥K",
    "♣J, ♣Q, ♣K, J., J., J.",
]


for notation in test_runs:
    meld = Card.from_test_notation(notation)
    print(f"\nRun\t{meld}")

    try:
        sprint(f"{Game.discover_runs(meld)}")
    except InvalidMeld as e:
        eprint(f"Error {e}")


game = Game(4)
game.shuffle_cards()

hand = game.draw_many(13)
hand.sort(key=lambda c: c.index)


def print_hand(cards):
    for i, card in enumerate(cards):
        print(f"{i: >2} {card}")


print_hand(hand)

while query := input():
    if not query or query == "q":
        break

    query = [x.strip() for x in query.split(" ")]
    command = query[0].lower()
    params = query[1:]

    if command == "m":
        indices = [int(i) for i in params]
        meld = [hand[i] for i in indices]

        try:
            score = Game.validate_set(meld)

            print(f"Set {meld}")

            hand = [card for i, card in enumerate(hand) if i not in indices]
        except InvalidMeld:
            eprint("Not a set")

        try:
            runs = Game.discover_runs(meld)

            print(f"Runs {runs}")

            hand = [card for i, card in enumerate(hand) if i not in indices]
        except InvalidMeld:
            eprint("Not a run")

        print_hand(hand)
    elif command == "d":
        discard_card = hand.pop(int(params[0]))

        print(f"Discarded {discard_card}")

        draw_card = game.draw_card()

        hand.append(draw_card)
        hand.sort(key=lambda c: c.index)

        print(f"Drew {draw_card}\n")

        print_hand(hand)
