import threading
from datetime import datetime


class Player:
    def __init__(self, name):
        self.name = name
        self.frames = [[] for _ in range(10)]

    def current_frame_index(self):
        for i in range(10):
            if self.frame_needs_more_throws(i):
                return i
        return None

    def frame_needs_more_throws(self, frame_idx):
        frame = self.frames[frame_idx]
        if frame_idx == 9:
            if len(frame) < 2:
                return True
            if len(frame) == 2:
                return frame[0] == 10 or frame[0] + frame[1] == 10
            return False
        if len(frame) == 0:
            return True
        if len(frame) == 1:
            return frame[0] != 10
        return False

    def frame_is_complete(self, frame_idx):
        return not self.frame_needs_more_throws(frame_idx)

    def is_finished(self):
        return all(not self.frame_needs_more_throws(i) for i in range(10))

    def validate_throw(self, pins):
        if not isinstance(pins, int) or pins < 0 or pins > 10:
            return "Los pinos deben ser un entero entre 0 y 10"
        frame_idx = self.current_frame_index()
        if frame_idx is None:
            return "Este jugador ya termino todos sus frames"
        frame = self.frames[frame_idx]
        if frame_idx == 9:
            if len(frame) == 1 and frame[0] != 10 and frame[0] + pins > 10:
                return f"Invalido: {frame[0]} + {pins} supera 10 pinos"
            if len(frame) == 2 and frame[0] == 10 and frame[1] != 10 and frame[1] + pins > 10:
                return f"Invalido: {frame[1]} + {pins} supera 10 pinos"
        else:
            if len(frame) == 1 and frame[0] != 10 and frame[0] + pins > 10:
                return f"Invalido: {frame[0]} + {pins} supera 10 pinos"
        return None

    def add_throw(self, pins):
        frame_idx = self.current_frame_index()
        if frame_idx is None:
            return None
        self.frames[frame_idx].append(pins)
        return frame_idx

    def get_all_throws(self):
        result = []
        for frame in self.frames:
            result.extend(frame)
        return result

    def calculate_scores(self):
        throws = self.get_all_throws()
        scores = [None] * 10
        cumulative = 0
        throw_idx = 0
        for frame_num in range(10):
            frame = self.frames[frame_num]
            if not frame:
                break
            if frame_num == 9:
                if not self.frame_needs_more_throws(9):
                    cumulative += sum(frame)
                    scores[frame_num] = cumulative
                break
            if frame[0] == 10:
                next_throws = throws[throw_idx + 1:throw_idx + 3]
                if len(next_throws) == 2:
                    cumulative += 10 + sum(next_throws)
                    scores[frame_num] = cumulative
                throw_idx += 1
            elif len(frame) == 2:
                if frame[0] + frame[1] == 10:
                    next_throws = throws[throw_idx + 2:throw_idx + 3]
                    if len(next_throws) == 1:
                        cumulative += 10 + next_throws[0]
                        scores[frame_num] = cumulative
                else:
                    cumulative += sum(frame)
                    scores[frame_num] = cumulative
                throw_idx += 2
            else:
                break
        return scores

    def get_current_throw_number(self):
        frame_idx = self.current_frame_index()
        if frame_idx is None:
            return None, None
        return frame_idx + 1, len(self.frames[frame_idx]) + 1


class BowlingGame:
    def __init__(self, num_players=4, player_names=None):
        self.lock = threading.Lock()
        self.num_players = num_players
        if player_names is None:
            player_names = [f"Jugador {i + 1}" for i in range(num_players)]
        self.players = [Player(name) for name in player_names]
        self.current_player_index = 0
        self.game_over = False
        self.log = []

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def add_throw(self, pins):
        with self.lock:
            if self.game_over:
                return {"ok": False, "error": "La partida ya termino. Inicie una nueva."}
            player = self.current_player
            err = player.validate_throw(pins)
            if err:
                return {"ok": False, "error": err}
            frame_idx = player.add_throw(pins)
            ts = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{ts}] {player.name} - Frame {frame_idx + 1}: {pins} pino(s)")
            if player.frame_is_complete(frame_idx):
                if self.current_player_index == self.num_players - 1:
                    self.current_player_index = 0
                    if all(p.is_finished() for p in self.players):
                        self.game_over = True
                        self.log.append(f"[{ts}] Partida terminada!")
                else:
                    self.current_player_index += 1
            return {"ok": True}

    def get_state(self):
        with self.lock:
            players_data = []
            for player in self.players:
                scores = player.calculate_scores()
                total = 0
                for s in reversed(scores):
                    if s is not None:
                        total = s
                        break
                frames_data = []
                for i in range(10):
                    frames_data.append({
                        "throws": list(player.frames[i]),
                        "score": scores[i],
                    })
                players_data.append({
                    "name": player.name,
                    "frames": frames_data,
                    "total": total,
                })
            cp = self.current_player
            frame_num, throw_num = cp.get_current_throw_number()
            return {
                "current_player": self.current_player_index,
                "current_player_name": cp.name,
                "current_frame": frame_num,
                "current_throw": throw_num,
                "game_over": self.game_over,
                "players": players_data,
                "log": self.log[-30:],
            }

    def reset(self, player_names=None):
        with self.lock:
            if player_names:
                self.players = [Player(name) for name in player_names]
            else:
                self.players = [Player(p.name) for p in self.players]
            self.current_player_index = 0
            self.game_over = False
            self.log = []
