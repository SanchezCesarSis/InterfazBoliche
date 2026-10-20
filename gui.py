import tkinter as tk


def format_throws(frame):
    if not frame:
        return ""
    result = []
    rack_start = 0
    for i, pins in enumerate(frame):
        if pins == 10:
            result.append("X")
            rack_start = i + 1
        elif i > rack_start and frame[i - 1] + pins == 10:
            result.append("/")
            rack_start = i + 1
        elif pins == 0:
            result.append("-")
        else:
            result.append(str(pins))
    return "  ".join(result)


class BowlingGUI:
    BG = "#0f0f23"
    CARD = "#1a1a2e"
    HEADER = "#16213e"
    HIGHLIGHT = "#1f2b4d"
    ACCENT = "#e94560"
    CYAN = "#00d2ff"
    FG = "#ffffff"
    DIM = "#8888aa"
    ERROR = "#ff6b6b"

    def __init__(self, game):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Boliche - Sistema de Puntuacion")
        self.root.geometry("1150x720")
        self.root.minsize(1050, 650)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.root.configure(bg=self.BG)

        tk.Label(
            self.root, text="BOLICHE  ·  SISTEMA DE PUNTUACION",
            font=("Segoe UI", 20, "bold"), bg=self.BG, fg=self.ACCENT,
        ).pack(pady=(14, 2))

        tk.Label(
            self.root, text="4 Jugadores  ·  10 Frames  ·  2 Tiros por Frame",
            font=("Segoe UI", 10), bg=self.BG, fg=self.DIM,
        ).pack()

        self.turn_label = tk.Label(
            self.root, text="", font=("Segoe UI", 15, "bold"),
            bg=self.HEADER, fg=self.CYAN, pady=10,
        )
        self.turn_label.pack(fill="x", padx=25, pady=10)

        self._build_scoreboard()
        self._build_log()
        self._build_controls()

    def _build_scoreboard(self):
        sb = tk.Frame(self.root, bg=self.CARD)
        sb.pack(fill="both", expand=True, padx=25, pady=(0, 5))

        sb.columnconfigure(0, weight=3)
        for i in range(1, 10):
            sb.columnconfigure(i, weight=2)
        sb.columnconfigure(10, weight=3)
        sb.columnconfigure(11, weight=2)

        headers = ["JUGADOR"] + [str(i) for i in range(1, 11)] + ["TOTAL"]
        for col, text in enumerate(headers):
            tk.Label(
                sb, text=text, font=("Segoe UI", 10, "bold"),
                bg=self.HEADER, fg=self.DIM, pady=7,
            ).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        self.name_labels = []
        self.throw_labels = []
        self.score_labels = []
        self.total_labels = []
        self.row_frames = []

        for row in range(4):
            name_lbl = tk.Label(
                sb, text=f"Jugador {row + 1}", font=("Segoe UI", 11, "bold"),
                bg=self.CARD, fg=self.FG, anchor="w", padx=12,
            )
            name_lbl.grid(row=row + 1, column=0, sticky="nsew", padx=1, pady=1)

            t_labels = []
            s_labels = []
            for col in range(10):
                cell = tk.Frame(sb, bg=self.CARD, bd=1, relief="groove")
                cell.grid(row=row + 1, column=col + 1, sticky="nsew", padx=1, pady=1)

                throw_lbl = tk.Label(
                    cell, text="", font=("Consolas", 10, "bold"),
                    bg=self.CARD, fg=self.FG, pady=3,
                )
                throw_lbl.pack(fill="x")

                score_lbl = tk.Label(
                    cell, text="", font=("Consolas", 13, "bold"),
                    bg=self.CARD, fg=self.ACCENT, pady=2,
                )
                score_lbl.pack(fill="x")

                t_labels.append(throw_lbl)
                s_labels.append(score_lbl)

            total_lbl = tk.Label(
                sb, text="0", font=("Segoe UI", 16, "bold"),
                bg=self.HEADER, fg=self.ACCENT, width=6,
            )
            total_lbl.grid(row=row + 1, column=11, sticky="nsew", padx=1, pady=1)

            self.name_labels.append(name_lbl)
            self.throw_labels.append(t_labels)
            self.score_labels.append(s_labels)
            self.total_labels.append(total_lbl)
            self.row_frames.append(sb)

        for i in range(5):
            sb.rowconfigure(i, weight=1)

    def _build_log(self):
        outer = tk.LabelFrame(
            self.root, text="  Registro de tiros  ", bg=self.CARD, fg=self.DIM,
            font=("Segoe UI", 9, "bold"), labelanchor="n",
        )
        outer.pack(fill="x", padx=25, pady=5)

        self.log_text = tk.Text(
            outer, height=6, bg="#0a0a1a", fg=self.DIM,
            font=("Consolas", 9), state="disabled", relief="flat",
        )
        scroll = tk.Scrollbar(outer, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.log_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

    def _build_controls(self):
        ctrl = tk.Frame(self.root, bg=self.BG)
        ctrl.pack(fill="x", padx=25, pady=(0, 4))

        tk.Button(
            ctrl, text="  Nueva Partida  ", command=self._reset,
            font=("Segoe UI", 10, "bold"), bg=self.ACCENT, fg=self.FG,
            activebackground="#c73e54", activeforeground=self.FG,
            relief="flat", cursor="hand2",
        ).pack(side="left")

        manual = tk.Frame(ctrl, bg=self.BG)
        manual.pack(side="right")

        tk.Label(
            manual, text="Pinos derribados:", font=("Segoe UI", 10),
            bg=self.BG, fg=self.DIM,
        ).pack(side="left", padx=(0, 5))

        self.pins_var = tk.IntVar(value=0)
        tk.Spinbox(
            manual, from_=0, to=10, textvariable=self.pins_var,
            width=3, font=("Segoe UI", 11, "bold"), justify="center",
        ).pack(side="left", padx=5)

        tk.Button(
            manual, text="  Registrar tiro  ", command=self._manual_throw,
            font=("Segoe UI", 10, "bold"), bg="#0f3460", fg=self.FG,
            activebackground="#1a4a80", activeforeground=self.FG,
            relief="flat", cursor="hand2",
        ).pack(side="left", padx=5)

        self.error_label = tk.Label(
            ctrl, text="", font=("Segoe UI", 9), bg=self.BG, fg=self.ERROR,
        )
        self.error_label.pack(side="bottom", fill="x")

    def _manual_throw(self):
        try:
            pins = self.pins_var.get()
        except tk.TclError:
            return
        result = self.game.add_throw(pins)
        if not result["ok"]:
            self.error_label.config(text=result["error"])
            self.error_label.after(4000, lambda: self.error_label.config(text=""))
        else:
            self.error_label.config(text="")
        self._refresh()

    def _reset(self):
        self.game.reset()
        self.error_label.config(text="")
        self._refresh()

    def _refresh(self):
        state = self.game.get_state()

        if state["game_over"]:
            winner = max(state["players"], key=lambda p: p["total"])
            self.turn_label.config(
                text=f"PARTIDA TERMINADA  ·  Ganador: {winner['name']} con {winner['total']} puntos",
                fg=self.ACCENT,
            )
        else:
            pname = state["current_player_name"]
            fnum = state["current_frame"]
            tnum = state["current_throw"]
            if fnum is not None and tnum is not None:
                self.turn_label.config(
                    text=f"Turno:  {pname}    |    Frame {fnum}    |    Tiro {tnum}",
                    fg=self.CYAN,
                )
            else:
                self.turn_label.config(text=f"Turno:  {pname}", fg=self.CYAN)

        for row in range(4):
            pdata = state["players"][row]
            is_current = row == state["current_player"] and not state["game_over"]
            row_bg = self.HIGHLIGHT if is_current else self.CARD
            prefix = "▶  " if is_current else ""
            fg_name = self.CYAN if is_current else self.FG

            self.name_labels[row].config(
                text=f"{prefix}{pdata['name']}", bg=row_bg, fg=fg_name,
            )

            for col in range(10):
                fdata = pdata["frames"][col]
                t_lbl = self.throw_labels[row][col]
                s_lbl = self.score_labels[row][col]
                t_lbl.config(bg=row_bg, text=format_throws(fdata["throws"]))
                s_lbl.config(bg=row_bg)
                if fdata["score"] is not None:
                    s_lbl.config(text=str(fdata["score"]), fg=self.ACCENT)
                else:
                    s_lbl.config(text="", fg="#555577")

            self.total_labels[row].config(text=str(pdata["total"]))

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        for entry in state["log"]:
            self.log_text.insert("end", entry + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

        self.root.after(400, self._refresh)

    def run(self):
        self.root.mainloop()
