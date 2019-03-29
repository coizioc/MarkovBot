"""Implements methods related to the deathmatch commands of miniscapebot.cogs.gastercoin."""
import random

from config import DEATHMATCH_FILE

DEATHMATCH_HEADER = '__**:anger:DEATHMATCH:anger:**__'

with open(DEATHMATCH_FILE, 'r', encoding='utf8') as f:
    file_string = f.read().splitlines()
    ATTACKS = []
    for line in file_string:
        split_line = line.split(';')
        try:
            ATTACKS.append((split_line[0], split_line[1]))
        except:
            print(line)

ATTACK_PROBABILITIES = [0] * 5 +\
                       [1] * 25 +\
                       [2] * 22 +\
                       [3] * 18 +\
                       [4] * 15 +\
                       [5] * 12 +\
                       [6] * 9 +\
                       [7] * 6 +\
                       [8] * 4 +\
                       [9] * 3 +\
                       [10] * 2 +\
                       [11]


def calculate_damage(power):
    """Calculates the amount of damage done based on its power from 0-10."""
    if power == 0:
        return 0
    elif power > 10:
        return 100
    else:
        damage = power * 3 + random.randint(-power, power)
        if damage < 0:
            damage = 0
        return damage


def do_deathmatch(fighter1, fighter2, bet=None):
    """Simulates each turn in a deathmatch and outputs the turns in the deathmatch as a list of strings."""
    is_fighter1turn = False
    fighter1_health = 100
    fighter2_health = 100

    deathmatch_messages = []

    current_message = f'{DEATHMATCH_HEADER}' \
                      f'\n\n\n\n' \
                      f'**{fighter1}**: {fighter1_health}/100\n**{fighter2}**: {fighter2_health}/100'

    previous_attack = '\n'
    deathmatch_messages.append(current_message)

    fighter1_turn_replace_list = [":arrow_right:", fighter1, fighter2]
    fighter2_turn_replace_list = [":arrow_left:", fighter2, fighter1]

    winner = None

    while True:
        # Chooses an appropriately powered attack.
        power = random.choice(ATTACK_PROBABILITIES)
        while True:
            attack = random.choice(ATTACKS)
            if int(attack[1]) == power:
                break
        current_attack = attack[0]

        if random.randint(0, 20) == 0:   # Randomly set attacks to miss.
            damage = 0
        elif "Infinity Gauntlet" in current_attack and random.randint(0, 1) == 0:   # Determines if Thanos spares you.
            damage = 0
        else:
            damage = calculate_damage(power)

        # Determine whose turn it is and replaces the names in the attack accordingly.
        if is_fighter1turn:
            replace_list = fighter1_turn_replace_list
            fighter2_health -= damage
        else:
            replace_list = fighter2_turn_replace_list
            fighter1_health -= damage
        if fighter1_health < 0:
            fighter1_health = 0
        if fighter2_health < 0:
            fighter2_health = 0

        current_attack = current_attack.replace('$P1', replace_list[1])
        current_attack = current_attack.replace('$P2', replace_list[2])
        # if '$SPECIAL' in current_attack:
        #     current_attack = current_attack.replace('$SPECIAL', replace_list[3])
        current_attack = replace_list[0] + current_attack

        is_fighter1turn ^= True
        if damage == 0 and power != 0:
            current_attack = current_attack[:-1] + ', but it misses!'
        current_attack += ' It does ' + str(damage) + ' damage.\n'

        # Prints the current turn and appends it to the list of turns.
        current_message = f'{DEATHMATCH_HEADER}\n\n{previous_attack}{current_attack}\n' \
                          f'**{fighter1}**: {fighter1_health}/100\n**{fighter2}**: {fighter2_health}/100'
        deathmatch_messages.append(current_message)
        previous_attack = current_attack

        # Checks if either fighter is dead and breaks the loop.
        if fighter2_health < 1:
            current_message += f'\n:trophy: **{fighter1} has won'
            if bet is not None:
                current_message += f' G${bet}!**'
            else:
                current_message += f'!**'
            deathmatch_messages.append(current_message)
            winner = fighter1
            break
        if fighter1_health < 1:
            current_message += f'\n:trophy: **{fighter2} has won'
            if bet is not None:
                current_message += f' G${bet}!**'
            else:
                current_message += f'!**'
            deathmatch_messages.append(current_message)
            winner = fighter2
            break
    return deathmatch_messages, winner
