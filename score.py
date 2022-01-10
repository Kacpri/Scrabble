class Score:
    def __init__(self):
        self._last_score = 0
        self._players_score = {}
        self._observers = []

    def set_players(self, players):
        self._players_score = {}
        for player in players:
            self._players_score[player] = []

    def add_points(self, player, points):
        player_score = self._players_score[player]
        current_score = player_score[-1] if player_score else 0
        new_score = current_score + points
        self._players_score[player].append(new_score)
        self.last_score = new_score

    def get_player_names(self):
        if not self._players_score:
            return ['Gracz', 'AI']
        return list(self._players_score)

    def swap_players(self):
        swapped = {}
        for player in reversed(self._players_score):
            swapped[player] = []
        self._players_score = swapped

    @property
    def last_score(self):
        return self._last_score

    @last_score.setter
    def last_score(self, value):
        self._last_score = value
        for callback in self._observers:
            callback(self._last_score)

    def bind_to(self, callback):
        self._observers.append(callback)
