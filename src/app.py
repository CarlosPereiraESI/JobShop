from flask import Flask, abort, jsonify, request

app = Flask(__name__)

simulations = [{'id': 0, 'nmachines': 1, 'njobs': 1, 'nops': 1}]
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
        return jsonify({'Error': "Simulation not found"}), 404
    simulations.remove(simulation[0])
    return jsonify({'result': True})


@app.route("/addoperation/<int:id_sim>/<int:id_job>", methods=['POST'])
def add_op(id_sim, id_job):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'Error': "Simulation not found"}), 404

    numjobs = simulation[0]['njobs']
    numops = simulation[0]['nops']   
    
    if (id_job < 0) or (id_job > numjobs):
        return jsonify({'Error': "Job not found"}), 404

    if not request.json or not 'id_op' or (request.json['id_op'] > numops) or not 'machine' or not 'time' in request.json:
        abort(400)
    operation = {
        'id_op': request.json['id_op'],
        'machine': request.json['machine'],
        'time': request.json['time'],
    }

    job = [job for job in jobs if job['id'] == id_job]

    if len(job) == 0:
        job = {
        'id': id_job,
        'operations': [operation]
        }
        jobs.append(job)
    else:
        for y in job[0]['operations']:
            if (y['id_op'] == operation['id_op']):
                return jsonify({'Error': "Operation Already Exists"}), 500
        job[0]['operations'].append(operation)

    return jsonify({'operation': operation})

@app.route("/createtable/<int:id_sim>", methods=['POST'])
def table(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'Error': "Simulation not found"}), 404

    numops = simulation[0]['nops']

    n = 0
    faults = False
    exists = False
    numbers = []
    misses = []
    while(n < numops):
        numbers.append(n)
        n += 1
    
    for x in jobs:       
        for i in numbers:     
            for y in x['operations']:        
                if y['id_op'] == i:
                    exists = True
            if (exists == False):
                misses.append({'job': x['id'], 'operation': i})
                faults = True
            exists = False 
    if (faults == False):
        return jsonify({'result': "Success, Table Completed!"}), 201
    else:
        return jsonify({'result': "Operation Missing", 'operations_missing': misses}), 500

@app.route("/jobs", methods=['GET'])
def list_table():
    return jsonify({'jobs': jobs})

@app.route("/updatetable/<int:id_job>/<int:id_op>", methods=['PUT'])
def update_op(id_job, id_op):
    if not request.json or not 'machine' or not 'time' in request.json:
        abort(400)

    job = [job for job in jobs if job['id'] == id_job]

    if len(job) == 0:
        return jsonify({'Error': "Operation not found"}), 404
    else:
        op = [op for op in job[0]['operations'] if op['id_op'] == id_op]
        if len(op) == 0:
            return jsonify({'Error': "Operation not found"}), 404
        else:
            op[0]['machine'] = request.json.get('machine', op[0]['machine'])
            op[0]['time'] = request.json.get('time', op[0]['time'])
            return jsonify({'machine': request.json['machine'], 'time': request.json['time']}), 201

if __name__ == '__main__':
    app.run(debug=True)
