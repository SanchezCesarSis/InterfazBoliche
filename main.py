import threading

from bowling import BowlingGame
from api import create_app
from gui import BowlingGUI


def main():
    game = BowlingGame(num_players=4)
    app = create_app(game)

    api_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
        daemon=True,
    )
    api_thread.start()

    print("=" * 60)
    print("  BOLICHE - Sistema de Puntuacion")
    print("=" * 60)
    print("  API activa en http://localhost:5000")
    print()
    print("  Endpoints para la camara/IA:")
    print("    POST /api/tiro      {\"pinos\": N}")
    print("    GET  /api/estado")
    print("    GET  /api/turno")
    print("    POST /api/jugadores {\"nombres\": [\"J1\",\"J2\",\"J3\",\"J4\"]}")
    print("    POST /api/reset")
    print("=" * 60)

    gui = BowlingGUI(game)
    gui.run()


if __name__ == "__main__":
    main()
