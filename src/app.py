from flask import Flask, abort, jsonify, request

app = Flask(__name__)

simulations = [
    {'id': 1, 'nmachines': 3, 'njobs': 3, 'nops': 3}]

jobs = []
ops = []

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
    
    numjobs = simulation['njobs']
    for i in range(numjobs):
        job = {
            'id': i,
            'operations': ops
        }
        jobs.append(job)
    simulations.append(simulation)
    return jsonify({'simulation': simulation}), 201

@app.route("/deletesim/<int:id_sim>", methods=['DELETE'])
def delete_sim(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        abort(404)
    simulations.remove(simulation[0])
    return jsonify({'result': True})

# @app.route("/createtable/<int:id_sim>", methods=['POST'])
# def create_table(id_sim):
#     simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
#     if len(simulation) == 0:
#         return jsonify({'result': "Simulation not found"}), 404
#     numjobs = simulation[0]['njobs']
#     numops = simulation[0]['nops']

#     for k in range(numops):
#         op = {
#             'id': k,
#             'machine': request.json['machine'],
#             'time': request.json['time']
#         }
#         ops.append(op)

#     for n in range(numjobs):
#         job = {
#             'id': n,
#             'operations': ops
#         }
#         jobs.append(job)
#     return jsonify({'jobs': jobs})


@app.route("/addoperation/<int:id_sim>/<int:id_job>", methods=['POST'])
def add_op(id_sim, id_job):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'result': "Simulation not found"}), 404
    numops = simulation[0]['nops']

    job = [job for job in jobs if job['id'] == id_job]
    if len(job) == 0:
       return jsonify({'result': "Job not found"}), 404 
    
    if not request.json or not 'id' or (request.json['id'] > numops) or not 'machine' or not 'time' in request.json:
        abort(400)
    operation = {
        'id': request.json['id'],
        'machine': request.json['machine'],
        'time': request.json['time'],
    }
    ops.append(operation)
    jobs.append(['operations'])
    return jsonify({'operation': operation})


@app.route("/table", methods=['GET'])
def table():
    return jsonify({'jobs': jobs})

if __name__ == '__main__':
    app.run(debug=True)
