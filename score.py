class Score:
    def __init__(self):
        self._last_score = 0
        self._players_score = {}
        self._player_names = ['AI', 'Gracz']
        for player in self._player_names:
            self._players_score[player] = []
        self._observers = {}

    @property
    def player_names(self):
        return self._player_names

    def get_score(self, player):
        return self._players_score[player][-1]

    def clear(self):
        for player in self._players_score:
            self._players_score[player].clear()

    def add_points(self, player, message, points):
        player_score = self._players_score[player]
        current_score = player_score[-1] if player_score else 0
        new_score = current_score + points
        self._players_score[player].append(new_score)
        self._last_score = new_score
        callback = self._observers.get(player)
        callback(message, points, self._last_score)

    @property
    def last_score(self):
        return self._last_score

    def bind_to(self, callback, player):
        self._observers[player] = callback
