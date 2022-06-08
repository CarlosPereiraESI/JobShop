from flask import Flask, abort, jsonify, request, send_file
import collections
from ortools.sat.python import cp_model


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
    if 'nmachines' in request.json and type(request.json['nmachines']) is not int:
        abort(400)
    if 'njobs' in request.json and type(request.json['njobs']) is not int:
        abort(400)
    if 'nops' in request.json and type(request.json['nops']) is not int:
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
    if 'id_op' in request.json and type(request.json['id_op']) is not int:
        abort(400)
    if 'machine' in request.json and type(request.json['machine']) is not int:
        abort(400)
    if 'time' in request.json and type(request.json['time']) is not int:
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
            if(y['machine'] == operation['machine']):
                return jsonify({'Error': "Machine Already Exists"}), 500
        job[0]['operations'].append(operation)

    return jsonify({'operation': operation})

@app.route("/createtable/<int:id_sim>", methods=['POST'])
def table(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'Error': "Simulation not found"}), 400

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
    if 'machine' in request.json and type(request.json['machine']) is not int:
        abort(400)
    if 'time' in request.json and type(request.json['time']) is not int:
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

@app.route("/readop/<int:id_job>/<int:id_op>", methods=['GET'])
def read_op(id_job, id_op):
    job = [job for job in jobs if job['id'] == id_job]
    if len(job) == 0:
        return jsonify({'Error': "Operation not found"}), 404
    else:
        op = [op for op in job[0]['operations'] if op['id_op'] == id_op]
        if len(op) == 0:
            return jsonify({'Error': "Operation not found"}), 404
        else:
            return jsonify({'machine': op[0]['machine'], 'time': op[0]['time']}), 201

@app.route("/downloadtable", methods=['GET'])
def download_table():
    f = open("src/table.txt", "w")
    
    for i in jobs:
        for y in i['operations']:
            f.write('(%s, %s)\t' % ((str)(y['machine']), (str)(y['time'])))
        f.write("\n")
    f.close()
    path = "table.txt"
    return send_file(path, as_attachment=True)

@app.route("/addstart/<int:id_job>/<int:id_op>", methods=['POST'])
def add_start(id_job, id_op):
    if not request.json or not 'start_time' in request.json:
            abort(400)
    if 'start_time' in request.json and type(request.json['start_time']) is not int:
        abort(400)

    start_time = request.json['start_time']
    job = [job for job in jobs if job['id'] == id_job]
    if len(job) == 0:
        return jsonify({'Error': "Job not found"}), 404
    else:
        op = [op for op in job[0]['operations'] if op['id_op'] == id_op]
        machine = op[0]['machine']
        if len(op) == 0:
            return jsonify({'Error': "Operation not found"}), 404
    sum = 0
    start_work = 1000
    end_work = 0

    for i in jobs:
        sum_other_jobs = 0
        for y in i['operations']:
            if("start_time" in y) and (id_job == i['id']):
                sum += (y['time'] + y['start_time'])
            if((id_job != i['id'])):
                sum_other_jobs += (y['time'] + y['start_time'])
                if(y['machine'] == machine):
                    start_work = sum_other_jobs - y['time']
                    end_work = sum_other_jobs
        
        print(sum_other_jobs)
        print(start_work)
        print(end_work)
        if (start_time >= sum) and ((start_time < start_work) or (start_time > end_work)):
            op[0]['start_time'] = start_time
            return jsonify({'start_time': start_time}), 201
        else:                
            return jsonify({'Error': "Invalid Start Time"}), 500

if __name__ == '__main__':
    app.run(debug=True)

