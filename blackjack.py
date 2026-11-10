"""Blackjack basic strategy advisor.

Strategy is stored as charts (rows x dealer upcards 2..A) so it can be
checked directly against a published chart. Rule variations are configurable.

Action codes:
    H = Hit, S = Stand, D = Double (hit if not allowed),
    X = Double (stand if not allowed), P = Split, R = Surrender
"""

import argparse
from dataclasses import dataclass

DEALER_ORDER = "23456789TA"  # column order of every chart below


@dataclass(frozen=True)
class Rules:
    dealer_hits_soft_17: bool = False   # False = S17, True = H17
    double_after_split: bool = True
    late_surrender: bool = False


def _chart(rows):
    return {key: dict(zip(DEALER_ORDER, row)) for key, row in rows.items()}


#                 2 3 4 5 6 7 8 9 T A
HARD = _chart({
    9:  "HDDDDHHHHH",
    10: "DDDDDDDDHH",
    11: "DDDDDDDDDH",   # H17 overrides the Ace column to D
    12: "HHSSSHHHHH",
    13: "SSSSSHHHHH",
    14: "SSSSSHHHHH",
    15: "SSSSSHHHHH",
    16: "SSSSSHHHHH",
})

SOFT = _chart({
    12: "HHHHHHHHHH",   # A,A when not split
    13: "HHHDDHHHHH",
    14: "HHHDDHHHHH",
    15: "HHDDDHHHHH",
    16: "HHDDDHHHHH",
    17: "HDDDDHHHHH",
    18: "SXXXXSSHHH",   # A,7: double 3-6 else stand
})

PAIRS_DAS = _chart({
    "A": "PPPPPPPPPP",
    "2": "PPPPPPHHHH",
    "3": "PPPPPPHHHH",
    "4": "HHHPPHHHHH",
    "6": "PPPPPHHHHH",
    "7": "PPPPPPHHHH",
    "8": "PPPPPPPPPP",
    "9": "PPPPPSPPSS",
})

PAIRS_NO_DAS = _chart({
    "A": "PPPPPPPPPP",
    "2": "HHPPPPHHHH",
    "3": "HHPPPPHHHH",
    "6": "HPPPPHHHHH",
    "7": "PPPPPPHHHH",
    "8": "PPPPPPPPPP",
    "9": "PPPPPSPPSS",
})
# 4s, 5s and 10s are never split (5s play as hard 10, 10s as hard 20).

ACTION_NAMES = {"H": "Hit", "S": "Stand", "D": "Double", "X": "Double",
                "P": "Split", "R": "Surrender"}


def normalize_rank(card):
    """Return one of 2-9, T, A. Accepts J/Q/K/10/T in any case, or None."""
    card = str(card).strip().upper()
    if card in ("10", "T", "J", "Q", "K"):
        return "T"
    if card in ("2", "3", "4", "5", "6", "7", "8", "9", "A"):
        return card
    return None


def evaluate(hand):
    """Return (best_total, is_soft) for a list of normalized ranks."""
    total = sum(1 if c == "A" else 10 if c == "T" else int(c) for c in hand)
    if "A" in hand and total + 10 <= 21:
        return total + 10, True
    return total, False


def hard_action(total, dealer, rules):
    if total <= 8:
        return "H"
    if total >= 17:
        return "S"
    if total == 11 and dealer == "A" and rules.dealer_hits_soft_17:
        return "D"
    return HARD[total][dealer]


def soft_action(total, dealer, rules):
    if total <= 18:
        return SOFT[total][dealer]
    if total == 19 and rules.dealer_hits_soft_17 and dealer == "6":
        return "X"
    return "S"


def pair_action(rank, dealer, rules):
    chart = PAIRS_DAS if rules.double_after_split else PAIRS_NO_DAS
    row = chart.get(rank)
    return row[dealer] if row and row[dealer] == "P" else None


def should_surrender(total, is_soft, dealer, rules):
    if not rules.late_surrender or is_soft:
        return False
    if total == 16 and dealer in "9TA":
        return True
    if total == 15 and dealer == "T":
        return True
    if rules.dealer_hits_soft_17 and dealer == "A" and total in (15, 17):
        return True
    return False


def basic_strategy(hand, dealer_up_card, rules=Rules(),
                   can_double=True, can_split=True, can_surrender=True):
    """Return 'H', 'S', 'D', 'P' or 'R' for the given hand and dealer upcard."""
    hand = [normalize_rank(c) for c in hand]
    dealer = normalize_rank(dealer_up_card)
    if dealer is None or None in hand or len(hand) < 2:
        raise ValueError("invalid cards")

    total, is_soft = evaluate(hand)
    if total > 21:
        raise ValueError("hand is bust")

    first_two = len(hand) == 2

    if first_two and can_split and hand[0] == hand[1]:
        if pair_action(hand[0], dealer, rules) == "P":
            return "P"

    if first_two and can_surrender and should_surrender(total, is_soft, dealer, rules):
        return "R"

    if is_soft:
        action = soft_action(total, dealer, rules)
    else:
        action = hard_action(total, dealer, rules)

    if not (first_two and can_double):
        if action == "D":
            action = "H"
        elif action == "X":
            action = "S"
    elif action == "X":
        action = "D"
    return action


def run_tests():
    s17, h17 = Rules(), Rules(dealer_hits_soft_17=True)
    no_das = Rules(double_after_split=False)
    surr = Rules(late_surrender=True)

    assert basic_strategy(["A", "7"], "3") == "D"
    assert basic_strategy(["A", "7"], "3", can_double=False) == "S"
    assert basic_strategy(["A", "7"], "9") == "H"
    assert basic_strategy(["A", "7"], "2") == "S"
    assert basic_strategy(["A", "6"], "5", can_double=False) == "H"
    assert basic_strategy(["A", "A"], "6", can_split=False) == "H"
    assert basic_strategy(["8", "8"], "10") == "P"
    assert basic_strategy(["10", "6"], "10") == "H"
    assert basic_strategy(["10", "6"], "10", surr) == "R"
    assert basic_strategy(["10", "4", "2"], "10", surr) == "H"
    assert basic_strategy(["8", "8"], "10", surr) == "P"
    assert basic_strategy(["5", "5"], "6") == "D"
    assert basic_strategy(["9", "2"], "A", s17) == "H"
    assert basic_strategy(["9", "2"], "A", h17) == "D"
    assert basic_strategy(["A", "8"], "6", h17) == "D"
    assert basic_strategy(["A", "8"], "6", s17) == "S"
    assert basic_strategy(["K", "Q"], "6") == "S"
    assert basic_strategy(["9", "9"], "7") == "S"
    assert basic_strategy(["4", "4"], "5") == "P"
    assert basic_strategy(["4", "4"], "5", no_das) == "H"
    assert basic_strategy(["2", "2"], "2", no_das) == "H"
    assert basic_strategy(["7", "2", "2"], "6", can_double=True) == "H"
    print("All tests passed.")


def main():
    parser = argparse.ArgumentParser(description="Blackjack basic strategy advisor")
    parser.add_argument("--h17", action="store_true",
                        help="dealer hits soft 17 (default: stands)")
    parser.add_argument("--no-das", action="store_true",
                        help="double after split not allowed")
    parser.add_argument("--surrender", action="store_true",
                        help="late surrender is available")
    parser.add_argument("--test", action="store_true", help="run self-tests and exit")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    rules = Rules(dealer_hits_soft_17=args.h17,
                  double_after_split=not args.no_das,
                  late_surrender=args.surrender)

    print("Blackjack Basic Strategy Advisor")
    print(f"Rules: dealer {'hits' if rules.dealer_hits_soft_17 else 'stands on'} soft 17, "
          f"DAS {'on' if rules.double_after_split else 'off'}, "
          f"surrender {'on' if rules.late_surrender else 'off'}")
    print("Enter your cards (e.g. 'A 7', '10,5', 'T 4 3') and the dealer's up card.")
    print("Use 2-10, J, Q, K, A (T also works for ten). Type 'quit' to exit.\n")

    while True:
        hand_input = input("Your hand: ").strip()
        if hand_input.lower() == "quit":
            break
        dealer_input = input("Dealer's up card: ").strip()
        if dealer_input.lower() == "quit":
            break

        tokens = hand_input.replace(",", " ").split()
        hand = [normalize_rank(t) for t in tokens]
        if len(hand) < 2:
            print("Please enter at least two cards.\n")
            continue
        if None in hand:
            bad = tokens[hand.index(None)]
            print(f"Invalid card: {bad}. Use 2-10, J, Q, K, A.\n")
            continue

        dealer = normalize_rank(dealer_input)
        if dealer is None:
            print("Invalid dealer card. Use 2-10, J, Q, K, A.\n")
            continue

        if evaluate(hand)[0] > 21:
            print("That hand is already bust.\n")
            continue

        action = basic_strategy(hand, dealer, rules)
        print(f"Recommended action: {ACTION_NAMES[action]}\n")

    print("Goodbye!")


if __name__ == "__main__":
    main()
