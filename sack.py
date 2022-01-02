from random import sample, choice


class Sack:
    values = {'A': 1, 'E': 1, 'I': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'W': 1, 'Z': 1, 'C': 2, 'D': 2, 'K': 2,
              'L': 2, 'M': 2, 'P': 2, 'T': 2, 'Y': 2, 'B': 3, 'G': 3, 'H': 3, 'J': 3, 'Ł': 3, 'U': 3, 'Ą': 5, 'Ę': 5,
              'F': 5, 'Ó': 5, 'Ś': 5, 'Ż': 5, 'Ć': 6, 'Ń': 7, 'Ź': 9, '_': 0}

    def __init__(self):
        self._letters = ['A'] * 9 + ['I'] * 8 + ['E'] * 7 + ['O'] * 6 + ['N', 'Z'] * 5 + ['R', 'S', 'W', 'Y'] * 4 + \
                        ['C', 'D', 'K', 'L', 'M', 'P', 'T'] * 3 + ['B', 'D', 'H', 'J', 'Ł', 'U', '_'] * 2 + \
                        ['Ą', 'Ę', 'Ć', 'F', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż']

    @staticmethod
    def values_without_blank():
        return list(Sack.values.keys())[:-1]

    def draw(self, quantity):
        if not self._letters:
            return None
        elif len(self._letters) < quantity:
            quantity = len(self._letters)

        drawn = sample(self._letters, quantity)
        self.remove_letters(drawn)

        return drawn

    def draw_one(self):
        if not self._letters:
            return None

        drawn = choice(self._letters)
        self._letters.remove(drawn)

        return drawn

    def remove_letters(self, letters_to_remove):
        for letter in letters_to_remove:
            self._letters.remove(letter)

    def exchange(self, rack, letters_to_exchange):
        if not letters_to_exchange:
            return rack
        if len(letters_to_exchange) > len(self._letters):
            return rack

        for letter in letters_to_exchange:
            rack.remove(letter)
        drawn = self.draw(len(letters_to_exchange))
        rack += drawn
        self._letters += letters_to_exchange
        return rack

