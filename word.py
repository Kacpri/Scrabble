class Word:
    def __init__(self, board):
        self.word = ''
        self.points = 0
        self.multiplier = 1
        self.tiles = {}
        self.start = None
        self.end = None
        self.direction = None
        self.board = board

    def add_letter(self, tile):
        self.word += tile.letter
        self.points += tile.points

    def multiply(self, multiplier):
        self.multiplier *= multiplier
