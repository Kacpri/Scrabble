class Score(object):
    def __init__(self, players):
        self._last_score = 10.0
        self._players_score = {}
        for player in players:
            self._players_score[player] = []
        self._observers = []

    def add_points(self, player, points):
        player_score = self._players_score[player]
        current_score = player_score[-1] if player_score else 0
        new_score = current_score + points
        self._players_score[player].append(new_score)
        self.last_score = new_score

    def get_player_names(self):

        return list(self._players_score)

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
