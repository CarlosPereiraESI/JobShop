from flask import Flask, abort, jsonify, request

app = Flask(__name__)

simulations = [
    {'id': 1, 'nmachines': 3, 'njobs': 3, 'nops': 3}
]

@app.route("/sims", methods=['GET'])
def list_sims():
    return jsonify({'simulations': simulations})

@app.route("/newsim", methods=['POST'])
def create_sims():
    if not request.json or not 'nmachines' or not 'njobs' or not 'nops' in request.json:
        abort(400)
    simulation = {
        'id': simulations[-1]['id'] + 1,
        'nmachines': request.json['nmachines'],
        'njobs': request.json['njobs'],
        'nops': request.json['nops']
    }
    if request.json['nmachines'] != request.json['njobs'] or request.json['nmachines'] != request.json['nops']:
        return({'result': "Machines, Jobs, Operations must be equal"}), 500
    simulations.append(simulation)
    return jsonify({'simulation': simulation}), 201

@app.route("/deletesim/<int:id_sim>", methods=['DELETE'])
def delete_sim(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        abort(404)
    simulations.remove(simulation[0])
    return jsonify({'result': True})

@app.route("/createtable/<int:id_sim>", methods=['POST'])
def create_table(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'result': "Simulation not found"}), 404
    

if __name__ == '__main__':
    app.run(debug=True)

