from flask import Flask, request, jsonify
from flask_cors import CORS
from Simulador import Simulator

app = Flask(__name__)
CORS(app)

vm = Simulator()

@app.route("/load", methods=["POST"])
def load_program():
    
    try:
        data = request.get_json()
        code = data.get("code", "")
        segments = data.get("segments", {})

        if not code.strip():
            return jsonify({"error": "Nenhum código recebido"}), 400

        vm.load_program_from_text(code, initial_segments=segments)

        vm.output_log = "programa carregado"

        return jsonify(vm.get_state_json())

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": f"Erro ao executar. Detalhe: {str(e)}",
            "detail": type(e).__name__,
            }), 500
    

@app.route("/run", methods=["POST"])
def run_program():
    
    try:
        vm.output_log = ''
        vm.run()

        return jsonify(vm.get_state_json())

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao executar. Detalhe: {str(e)}",
            "detail": type(e).__name__,
            }), 500
    

@app.route("/step", methods=["POST"])
def step():
   
    try:
        vm.output_log = ''
        vm.step()
        
        return jsonify(vm.get_state_json())
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao executar. Detalhe: {str(e)}",
            "detail": type(e).__name__,
            }), 500


@app.route("/reset", methods=["POST"])
def reset_program():

    global vm
    vm = Simulator() 

    return jsonify(vm.get_state_json())


@app.route("/dump", methods=["POST"])
def dump_program():

    try:
        return jsonify(vm.get_state_json())

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao executar. Detalhe: {str(e)}",
            "detail": type(e).__name__,
            }), 500


if __name__ == "__main__":
    app.run(debug=True)