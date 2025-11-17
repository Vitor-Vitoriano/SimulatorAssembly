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

        return jsonify({"status": "program loaded", "instructions": len(vm.program)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/run", methods=["POST"])
def run_program():

    try:
        vm.run()
        return jsonify({
            "status": "program executed",
            "registers": vm.cpu.dump()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/step", methods=["POST"])
def step():
   
    try:
        vm.step()

        return jsonify({
            "status": "step executed",
            "registers": vm.cpu.dump(),
            "ip": vm.cpu.get_reg("ip")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset_program():

    global vm
    vm = Simulator()  

    return jsonify({"status": "reset done"})


@app.route("/dump", methods=["GET"])
def dump_program():

    try:
        return jsonify({
            "registers": vm.cpu.dump(),
            "ip": vm.cpu.get_reg("ip"),
            "program_size": len(vm.program)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)