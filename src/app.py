from flask import Flask, abort, jsonify, request

app = Flask(__name__)

simulations = [{'id': 0, 'nmachines': 1, 'njobs': 1, 'nops': 1}]
ops = []
jobs = []

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


@app.route("/addoperation/<int:id_sim>/<int:id_job>", methods=['POST'])
def add_op(id_sim, id_job):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'result': "Simulation not found"}), 404

    numjobs = simulation[0]['njobs']
    numops = simulation[0]['nops']
    
    if not request.json or not 'id_op' or (request.json['id_op'] > numops) or not 'machine' or not 'time' in request.json:
        abort(400)
    operation = {
        'id_op': request.json['id_op'],
        'machine': request.json['machine'],
        'time': request.json['time'],
    }

    for y in jobs:
        for x in y['operations']:
            if x['id_op'] == request.json['id_op']:
                return jsonify({'result': "Operation Already Exists"})

    job = {
        'id': id_job,
         'operations': [operation]
    }
    jobs.append(job)   
    return jsonify({'operation': operation})
    # else:
    #     return jsonify({'result': "Operation Already Exists"}), 500

@app.route("/table", methods=['GET'])
def table():
    return jsonify({'jobs': jobs})

if __name__ == '__main__':
    app.run(debug=True)
