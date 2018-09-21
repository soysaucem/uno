import random
from enum import Enum

from a2 import Card, SkipCard, ReverseCard, Pickup2Card, Pickup4Card
from a2 import Deck

__author__ = "Brae Webb"


class CardColour(Enum):
    """
    An enumeration of card colours in the Uno game.
    """
    blue = "#508ebf"
    red = "#a30e15"
    yellow = "#f9bf3b"
    green = "#5d8402"
    black = "#222"


FULL_DECK = [
    (Card(0, CardColour.red), (0, 10)),
    (Card(0, CardColour.yellow), (0, 10)),
    (Card(0, CardColour.green), (0, 10)),
    (Card(0, CardColour.blue), (0, 10)),
    (Card(0, CardColour.red), (1, 10)),
    (Card(0, CardColour.yellow), (1, 10)),
    (Card(0, CardColour.green), (1, 10)),
    (Card(0, CardColour.blue), (1, 10)),

    (SkipCard(0, CardColour.red), (0, 2)),
    (SkipCard(0, CardColour.yellow), (0, 2)),
    (SkipCard(0, CardColour.green), (0, 2)),
    (SkipCard(0, CardColour.blue), (0, 2)),

    (ReverseCard(0, CardColour.red), (0, 2)),
    (ReverseCard(0, CardColour.yellow), (0, 2)),
    (ReverseCard(0, CardColour.green), (0, 2)),
    (ReverseCard(0, CardColour.blue), (0, 2)),

    (Pickup2Card(0, CardColour.red), (0, 2)),
    (Pickup2Card(0, CardColour.yellow), (0, 2)),
    (Pickup2Card(0, CardColour.green), (0, 2)),
    (Pickup2Card(0, CardColour.blue), (0, 2)),

    (Pickup4Card(0, CardColour.black), (0, 2)),
    (Pickup4Card(0, CardColour.black), (0, 2)),
    (Pickup4Card(0, CardColour.black), (0, 2)),
    (Pickup4Card(0, CardColour.black), (0, 2)),
]

SPECIAL_CARDS = [Pickup4Card]


class TurnManager:
    """
    A class to manage the order of turns amongst game players.
    """
    def __init__(self, players):
        """
        Construct a new turn manager to based on game players.

        Parameters:
             players (list<T>): An ordered list of players to store.
        """
        self._players = players
        # start in correct direction
        self._direction = True
        self._location = 0
        self._max = len(players)

    def current(self):
        """
        (T) Returns the player whose turn it is.
        """
        return self._players[self._location]

    def next(self):
        """
        (T) Moves onto the next players turn and return that player.
        """
        return self.skip(count=0)

    def peak(self, count=1):
        """
        Look forward or backwards in the current ordering of turns.

        Parameters:
            count (int): The amount of turns to look forward,
                         if negative, looks backwards.

        Returns:
            (T): The player we are peaking at.
        """
        location = self._location
        location += count if self._direction else -count
        location %= self._max
        return self._players[location]

    def reverse(self):
        """
        Reverse the order of turns.
        """
        self._direction = not self._direction

    def skip(self, count=0):
        """
        (T): Moves onto the next player, skipping 'count' amount players.
        """
        count += 1
        self._location += count if self._direction else -count
        self._location %= self._max
        return self._players[self._location]


class UnoGame:
    """
    A game of Uno++.
    """
    def __init__(self, deck, players):
        """
        Construct a game of uno from a pickup pile and list of players.

        Parameters:
            deck (Deck): The pile of cards to pickup from.
            players (list<Player>): The players in this game of uno.
        """
        self.pickup_pile = deck
        self.players = players

        self._turns = TurnManager(players)

        self.putdown_pile = Deck(self.pickup_pile.pick())
        self.special_pile = Deck()

        self._is_over = False
        self.winner = None

    def next_player(self):
        """
        Changes to the next player in the game and returns an instance of them.

        Returns:
            (Player): The next player in the game.
        """
        return self._turns.next()

    def current_player(self):
        """
        (Player) Returns the player whose turn it is currently.
        """
        return self._turns.current()

    def skip(self):
        """Prevent the next player from taking their turn."""
        self._turns.skip()

    def reverse(self):
        """Transfer the turn back to the previous player and reverse the order."""
        self._turns.reverse()

    def get_turns(self):
        """(TurnManager) Returns the turn manager for this game."""
        return self._turns

    def is_over(self):
        """
        (bool): True iff the game has been won. Assigns the winner variable.
        """
        for player in self.players:
            if player.has_won():
                self.winner = player
                self._is_over = True

        return self._is_over

    def select_card(self, player, card):
        """Perform actions for a player selecting a card

        Parameters:
            player (Player): The selecting player.
            card (Card): The card to select.
        """
        card.play(player, self)
        if card.__class__ in SPECIAL_CARDS:
            self.special_pile.add_card(card)
        else:
            self.putdown_pile.add_card(card)

    def take_turn(self, player):
        """
        Takes the turn of the given player by having them select a card.

        Parameters:
            player (Player): The player whose turn it is.
        """
        card = player.pick_card(self.putdown_pile)

        if card is None:
            player.get_deck().add_cards(self.pickup_pile.pick())
            return

        if card.matches(self.putdown_pile.top()):
            self.select_card(player, card)

    def take_turns(self):
        """
        Plays an entire round by taking the turn for each player in the game.
        """
        for player in self.players:
            self.take_turn(player)

            if player.has_won():
                return


def build_deck(structure, range_cards=(Card, )):
    """
    Construct a deck from a simplified deck structure.

    Example structure:
    [ (Card(colour=CardColour.red), (0, 10)),
      (SkipCard(colour=CardColour.green), (3, 5)) ]

    Creates a deck with red cards numbered from 0 up to but not including 10 and
    skip cards with the numbers 3 and 4. Assuming both cards are in range_cards,
    otherwise creates the same amount of cards with -1 as their numbers.

    Parameters:
        structure (list<tuple>): The simplified deck structure.
        range_cards (tuple<Card>): Cards whose numbers should be updated from -1.
    """
    deck = []

    for (card, (start, end)) in structure:
        for number in range(start, end):
            new_card = card.__class__(-1, card.get_colour())
            if card.__class__ in range_cards:
                new_card.set_number(number)
            deck.append(new_card)

    return deck


def generate_name():
    """
    (str): Selects a random name from a list of player names.
    """
    with open("players.txt", "r") as file:
        names = file.readlines()
    return random.choice(names).strip()


def main():
    print("Please run gui.py instead")


if __name__ == "__main__":
    main()
