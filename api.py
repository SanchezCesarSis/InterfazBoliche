from flask import Flask, jsonify, request


def create_app(game):
    app = Flask(__name__)

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/api/tiro", methods=["POST"])
    def registrar_tiro():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"ok": False, "error": "Se espera JSON con el campo 'pinos'"}), 400
        pins = data.get("pinos")
        if pins is None:
            return jsonify({"ok": False, "error": "Falta el campo 'pinos'"}), 400
        try:
            pins = int(pins)
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "'pinos' debe ser un numero entero"}), 400
        result = game.add_throw(pins)
        return jsonify(result), (200 if result["ok"] else 400)

    @app.route("/api/estado", methods=["GET"])
    def obtener_estado():
        return jsonify(game.get_state())

    @app.route("/api/turno", methods=["GET"])
    def obtener_turno():
        state = game.get_state()
        return jsonify({
            "jugador": state["current_player_name"],
            "indice": state["current_player"],
            "frame": state["current_frame"],
            "tiro": state["current_throw"],
            "game_over": state["game_over"],
        })

    @app.route("/api/reset", methods=["POST"])
    def resetear():
        data = request.get_json(silent=True) or {}
        nombres = data.get("nombres")
        if nombres is not None:
            if not isinstance(nombres, list) or len(nombres) != 4:
                return jsonify({"ok": False, "error": "Se requieren exactamente 4 nombres"}), 400
        game.reset(nombres)
        return jsonify({"ok": True})

    @app.route("/api/jugadores", methods=["POST"])
    def set_jugadores():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"ok": False, "error": "Se espera JSON con 'nombres'"}), 400
        nombres = data.get("nombres")
        if not isinstance(nombres, list) or len(nombres) != 4:
            return jsonify({"ok": False, "error": "Se requieren exactamente 4 nombres"}), 400
        game.reset(nombres)
        return jsonify({"ok": True})

    return app
