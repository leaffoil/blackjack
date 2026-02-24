def normalize_dealer_card(card):
    if card in ['J', 'Q', 'K', '10']:
        return '10'
    return str(card)

def hard_action(total, dealer):
    dealer = normalize_dealer_card(dealer)
    if total <= 8:
        return 'H'
    elif total == 9:
        return 'D' if dealer in ['3', '4', '5', '6'] else 'H'
    elif total == 10:
        return 'D' if dealer in ['2', '3', '4', '5', '6', '7', '8', '9'] else 'H'
    elif total == 11:
        return 'D'
    elif total == 12:
        return 'S' if dealer in ['4', '5', '6'] else 'H'
    elif 13 <= total <= 16:
        return 'S' if dealer in ['2', '3', '4', '5', '6'] else 'H'
    else:
        return 'S'

def soft_action(soft_total, dealer):
    dealer = normalize_dealer_card(dealer)
    if soft_total in (13, 14):
        return 'D' if dealer in ['5', '6'] else 'H'
    elif soft_total in (15, 16):
        return 'D' if dealer in ['4', '5', '6'] else 'H'
    elif soft_total == 17:
        return 'D' if dealer in ['3', '4', '5', '6'] else 'H'
    elif soft_total == 18:
        if dealer in ['3', '4', '5', '6']:
            return 'D'
        elif dealer in ['2', '7', '8']:
            return 'S'
        else:
            return 'H'
    else:
        return 'S'

def pair_action(pair_rank, dealer):
    dealer = normalize_dealer_card(dealer)
    if pair_rank in ('A', '8'):
        return 'P'
    elif pair_rank in ('2', '3'):
        return 'P' if dealer in ['2', '3', '4', '5', '6', '7'] else None
    elif pair_rank == '4':
        return 'P' if dealer in ['5', '6'] else None
    elif pair_rank == '5':
        return None
    elif pair_rank == '6':
        return 'P' if dealer in ['2', '3', '4', '5', '6'] else None
    elif pair_rank == '7':
        return 'P' if dealer in ['2', '3', '4', '5', '6', '7'] else None
    elif pair_rank == '9':
        if dealer in ['2', '3', '4', '5', '6', '8', '9']:
            return 'P'
        else:
            return None
    elif pair_rank == '10':
        return None
    else:
        return None

def basic_strategy(hand, dealer_up_card, can_double=True, can_split=True):
    dealer = normalize_dealer_card(dealer_up_card)
    if len(hand) == 2 and can_split and hand[0] == hand[1]:
        split_decision = pair_action(hand[0], dealer)
        if split_decision == 'P':
            return 'P'
    total = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
            total += 1
        else:
            if card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
    soft_total = total + 10 if ace_count > 0 and total + 10 <= 21 else None
    is_soft = soft_total is not None
    if len(hand) != 2:
        can_double = False
    if is_soft:
        action = soft_action(soft_total, dealer)
    else:
        action = hard_action(total, dealer)
    if action == 'D' and not can_double:
        action = 'H'
    return action

def parse_card(card_str):
    card = card_str.strip().upper()
    if card in ['J', 'Q', 'K', 'A']:
        return card
    elif card == '10':
        return '10'
    elif card in ['2','3','4','5','6','7','8','9']:
        return card
    else:
        return None

def main():
    print("Blackjack Basic Strategy Advisor")
    print("Enter your hand (two cards, e.g., 'A 7' or '10,5') and the dealer's up card.")
    print("Type 'quit' to exit.\n")
    
    while True:
        hand_input = input("Your hand: ").strip()
        if hand_input.lower() == 'quit':
            break
        dealer_input = input("Dealer's up card: ").strip()
        if dealer_input.lower() == 'quit':
            break
        
        # Parse hand
        hand_cards = hand_input.replace(',', ' ').split()
        if len(hand_cards) != 2:
            print("Please enter exactly two cards for your hand.\n")
            continue
        
        parsed_hand = []
        valid = True
        for c in hand_cards:
            pc = parse_card(c)
            if pc is None:
                print(f"Invalid card: {c}")
                valid = False
                break
            parsed_hand.append(pc)
        if not valid:
            print("Use 2-10, J, Q, K, A.\n")
            continue
        
        # Parse dealer card
        dealer_card = parse_card(dealer_input)
        if dealer_card is None:
            print("Invalid dealer card. Use 2-10, J, Q, K, A.\n")
            continue
        
        action_code = basic_strategy(parsed_hand, dealer_card)
        if action_code == 'H':
            action = "Hit"
        elif action_code == 'S':
            action = "Stand"
        elif action_code == 'D':
            action = "Double"
        elif action_code == 'P':
            action = "Split"
        else:
            action = "Unknown"
        
        print(f"Recommended action: {action}\n")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()