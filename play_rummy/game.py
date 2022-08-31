from collections import defaultdict
import random

CARD_SUITS = ["♣", "♦", "♥", "♠"]
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

NUM_DECKS = 2

NUM_SUITS = len(CARD_SUITS)
NUM_RANKS = len(CARD_RANKS)
NUM_JOKERS = 3

NUM_SUIT_CARDS = NUM_SUITS * NUM_RANKS
NUM_CARDS_PER_DECK = NUM_SUITS * NUM_RANKS + NUM_JOKERS
NUM_CARDS = NUM_DECKS * NUM_CARDS_PER_DECK


class InvalidMeld(Exception):
    pass


class Card:
    def __init__(self, suit, rank) -> None:
        self.suit = suit
        self.rank = rank

    @staticmethod
    def identify_card(card_index):
        deck_index = card_index % NUM_CARDS_PER_DECK

        if deck_index >= NUM_SUIT_CARDS:
            return Card(NUM_SUITS, deck_index - NUM_SUIT_CARDS)
        else:
            card_suit = deck_index // NUM_RANKS
            card_rank = deck_index % NUM_RANKS
            return Card(card_suit, card_rank)

    @staticmethod
    def reverse_notation(notation):
        if notation == "J.":
            return Card(NUM_SUITS, 0)
        else:
            return Card(CARD_SUITS.index(notation[0]), CARD_RANKS.index(notation[1:]))

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
    def aces_of(cards):
        return [card for card in cards if card.is_ace]
        
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
        return Card.identify_card(self.cards.pop())

    def draw_many(self, num_cards):
        return [self.draw_card() for _ in range(num_cards)]

    @staticmethod
    def validate_set(cards):
        if Card.has_duplicates(cards):
            raise InvalidMeld("duplicate cards")

        if len(cards) < 3 or len(cards) > 4:
            raise InvalidMeld("not of length 3 or 4")

        regulars = Card.regulars_of(cards)

        if len(regulars) < 2:
            raise InvalidMeld("too many jokers")

        if Card.are_ranks_matching(regulars):
            raise InvalidMeld("mismatching ranks")

        return regulars[0].score * len(cards)

    @staticmethod
    def validate_run(cards):
        if Card.has_duplicates(cards):
            raise InvalidMeld("duplicate cards")

        if len(cards) < 3 or len(cards) > NUM_RANKS:
            raise InvalidMeld(f"not of length 3 to {NUM_RANKS}")

        regulars = Card.regulars_of(cards)
        commons = Card.commons_of(cards)

        if len(commons) < 2:
            raise InvalidMeld("too few regular cards")

        if Card.are_suits_matching(regulars):
            raise InvalidMeld("mismatching suits in regulars")

        sorted_commons = Card.sort_by_rank(commons)

        jokers = Card.jokers_of(cards)
        ace = Card.first_ace(cards)

        if not ace:
            runs = [sorted_commons]
        else:
            runs = [[ace, *sorted_commons], [*sorted_commons, ace]]

        validated_runs = []

        for run in runs:
            available_jokers = [*jokers]
            validated_run = []

            for card in run:
                # print(f"{i: >3} {card}")

                if len(validated_run) > 0:
                    if validated_run[-1].is_joker:
                        # print("Joker")
                        rank_change = 1
                    else:
                        rank_change = card.rank - validated_run[-1].rank

                    # print(f"{rank_change: >6}")

                    if rank_change > 1:
                        if len(available_jokers) >= rank_change - 1:
                            for _ in range(rank_change - 1):
                                validated_run.append(available_jokers.pop())
                        else:
                            validated_run = None
                            break
                    elif not (rank_change == 1 or rank_change == -NUM_RANKS + 1):
                        validated_run = None
                        break

                validated_run.append(card)

            if validated_run and available_jokers:
                if not validated_run[-1].is_ace:
                    validated_run = [*validated_run, *available_jokers]
                elif not validated_run[0].is_ace:
                    validated_run = [*available_jokers, *validated_run]

            if validated_run:
                validated_runs.append(validated_run)

        print(validated_runs)

        if not validated_runs:
            raise InvalidMeld("no valid run possible")

        return 0


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
    print(f"Set\t{meld}")

    try:
        print(f"Score {Game.validate_set(meld)}")
    except InvalidMeld as e:
        print(f"Error {e}")


test_runs = [
    "♣2, ♦2",
    "♣2, ♦2",
    "♣A, ♦2, ♥3",
    "♣A, ♣2, ♣3",
    "♣A, ♣2, ♣3, ♣3",
    "♣A, ♣2, ♣3, ♣4, ♣5",
    "♣A, ♣2, ♣3, J., ♣5",
    "♣A, ♣2, ♣3, J., ♣4",
    "♣A, ♣2, ♣3, J., ♣Q",
    "♣A, ♣J, ♣Q, J., ♣K",
    "♣A, ♣10, ♣J, J., ♣Q",
    "♣A, ♣2, J., ♣4, ♣5, J., ♣7, J., J.",
    "♣A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣K, ♣Q, J.",
    "♥A, ♣2, ♣3, ♣4, ♣5, ♣6, ♣7, ♣8, ♣9, ♣10, ♣J, ♣K, J.",
    "♥10, J., J., ♥Q",
    "♥10, J., J., ♥K",
]


for notation in test_runs:
    meld = Card.from_test_notation(notation)
    print(f"Run\t{meld}")

    try:
        print(f"Score {Game.validate_run(meld)}")
    except InvalidMeld as e:
        print(f"Error {e}")


game = Game(4)
game.shuffle_cards()

hand = game.draw_many(13)
hand.sort(key=lambda c: c.index % NUM_CARDS_PER_DECK)

for i, card in enumerate(hand):
    print(f"{i: >2} {card}")

while choice := input():
    if choice == "q":
        break

    choices = [choice.strip() for choice in choice.split(",")]

    meld = [hand[int(i)] for i in choices]

    try:
        print(Game.validate_set(meld))
    except InvalidMeld as e:
        print(f"Not a set")

    try:
        print(Game.validate_run(meld))
    except InvalidMeld as e:
        print(f"Not a run")
