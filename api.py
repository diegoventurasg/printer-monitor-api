from flask import Flask, jsonify, abort
from printers import PRINTERS
from toner_monitor import check_printer_toners

app = Flask(__name__)

@app.route("/printers", methods=["GET"])
def list_printers():
    return jsonify(PRINTERS), 200

@app.route("/printer/<int:printer_id>", methods=["GET"])
def printer_status(printer_id):
    printer = next((p for p in PRINTERS if p["id"] == printer_id), None)
    if not printer:
        return jsonify({
            "error": "Not Found",
            "message": "Impressora não encontrada",
        }), 404

    niveis = {}
    try:
        niveis = check_printer_toners(printer["ip"])
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "Não foi possível obter os dados da impressora no momento"
        }), 500

    order = ["Amarelo", "Magenta", "Ciano", "Preto"]
    toners = {}
    alertas = []

    if isinstance(niveis, dict):        
        for name in order:
            if name in niveis:
                toners[name.lower()] = niveis[name]
                level = niveis[name]
                if level < 10:
                    alertas.append(f"{name}: Toner Indisponível")
                elif level < 15:
                    alertas.append(f"{name} ({level}%)")

    response = {
        "id": printer["id"],
        "nome": printer["nome"],
        "modelo": printer["modelo"],
        "ip": printer["ip"],
        "local": printer["local"],
        "status": "online" if niveis is not None else "offline",
        "alertas": alertas,
        "color": printer["color"],
        "toners": toners
    }
    return jsonify(response), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)