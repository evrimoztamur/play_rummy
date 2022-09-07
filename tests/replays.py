from play_rummy.game import (
    DiscardAction,
    MeldAction,
    PickUpAction,
    PickUpTarget,
)


TEST_REPLAYS = [
    (
        1,
        4,
        [
            DiscardAction(0),
            PickUpAction(PickUpTarget.DISCARD),
            PickUpAction(PickUpTarget.DECK),
            PickUpAction(PickUpTarget.DECK),
            MeldAction([0, 3, 7]),
            MeldAction([0, 4, 7]),
            DiscardAction(9),
            PickUpAction(PickUpTarget.DISCARD),
            PickUpAction(PickUpTarget.DISCARD),
            PickUpAction(PickUpTarget.DECK),
            MeldAction([0, 5, 8]),
            DiscardAction(10),
            PickUpAction(PickUpTarget.DECK),
            MeldAction([3, 5, 9, 12]),
            MeldAction([0, 3, 4, 7]),
            DiscardAction(5),
            PickUpAction(PickUpTarget.DISCARD),
            MeldAction([5, 6, 10, 11]),
            MeldAction([2, 8, 9]),
            DiscardAction(4),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(2),
            PickUpAction(PickUpTarget.DISCARD),
            DiscardAction(11),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(5),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(3),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(12),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(0),
            PickUpAction(PickUpTarget.DISCARD),
            MeldAction([0, 1, 5]),
            DiscardAction(2),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(3),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(4),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(13),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(2),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(6),
            PickUpAction(PickUpTarget.DISCARD),
            DiscardAction(12),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(0),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(2),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(6),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(9),
            PickUpAction(PickUpTarget.DECK),
            DiscardAction(6),
            PickUpAction(PickUpTarget.DISCARD),
            MeldAction([0, 1, 2]),
        ],
    )
]
