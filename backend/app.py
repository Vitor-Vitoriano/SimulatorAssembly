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

        if not code.strip():
            return jsonify({"error": "Nenhum código recebido"}), 400

        vm.load_program_from_text(code)

        return jsonify({"output": "programa carregado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/run", methods=["POST"])
def run_program():
    
    try:
        vm.run()
        return jsonify({
            "instructions": vm.output_log,
            "registers": vm.cpu.dump(),
            "output": "programa executado"        
        })

    except Exception as e:
        return jsonify({"error": f"erro na instrução:{vm.output_log}"+str(e)}), 500
    

@app.route("/step", methods=["POST"])
def step():
   
    try:
        vm.output_log = ''
        vm.step()
        

        return jsonify({
            "instruction": vm.output_log,
            "registers": vm.cpu.dump(),
            "output": "step executado",
        })
    except Exception as e:
        return jsonify({"error": f"erro na instrução:{vm.output_log}"+str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset_program():

    global vm
    vm = Simulator()  

    return jsonify({
        "registers": vm.cpu.dump(),
        "output": "reset",
        })


@app.route("/dump", methods=["GET"])
def dump_program():

    try:
        return jsonify({
            "registers": vm.cpu.dump(),
            "output": "dump realizado",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)