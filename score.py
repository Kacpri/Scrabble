class Score:
    def __init__(self):
        self._last_score = 0
        self._players_score = {}
        self._player_names = ['AI', 'Gracz']
        for player in self._player_names:
            self._players_score[player] = []
        self._observers = []

    @property
    def player_names(self):
        return self._player_names

    def get_score(self, player):
        return self._players_score[player][-1]

    def set_player_names(self, players):
        self._player_names = players

    def clear(self):
        for player in self._players_score:
            self._players_score[player].clear()

    def add_points(self, player, points):
        player_score = self._players_score[player]
        current_score = player_score[-1] if player_score else 0
        new_score = current_score + points
        self._players_score[player].append(new_score)
        self._last_score = new_score
        for callback in self._observers:
            callback(self._last_score)

    @property
    def last_score(self):
        return self._last_score

    def bind_to(self, callback):
        self._observers.append(callback)
