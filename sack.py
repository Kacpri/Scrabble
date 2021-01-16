from random import sample, choice


class Sack:
    values = {'_': 0, 'A': 1, 'E': 1, 'I': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'W': 1, 'Z': 1, 'C': 2, 'D': 2, 'K': 2,
              'L': 2, 'M': 2, 'P': 2, 'T': 2, 'Y': 2, 'B': 3, 'G': 3, 'H': 3, 'J': 3, 'Ł': 3, 'U': 3, 'Ą': 5, 'Ę': 5,
              'F': 5, 'Ó': 5, 'Ś': 5, 'Ż': 5, 'Ć': 6, 'Ń': 7, 'Ź': 9}

    def __init__(self):
        self._letters = ['A'] * 9 + ['I'] * 8 + ['E'] * 7 + ['O'] * 6 + ['N', 'Z'] * 5 + ['R', 'S', 'W', 'Y'] * 4 + \
                        ['C', 'D', 'K', 'L', 'M', 'P', 'T'] * 3 + ['B', 'D', 'H', 'J', 'Ł', 'U', '_'] * 2 + \
                        ['Ą', 'Ę', 'Ć', 'F', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż']
        self._letters.sort()

    def draw(self, n):
        if not self._letters:
            return None
        elif len(self._letters) < n:
            n = len(self._letters)

        drawn = sample(self._letters, n)

        for letter in drawn:
            self._letters.remove(letter)

        return drawn

    def draw_one(self):
        if not self._letters:
            return None

        drawn = choice(self._letters)
        self._letters.remove(drawn)

        return drawn

    def exchange(self, letters_to_exchange):
        drawn = self.draw(len(letters_to_exchange))
        self._letters += letters_to_exchange

        return drawn
