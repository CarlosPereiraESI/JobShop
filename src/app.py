from flask import Flask, abort, jsonify, request, send_file, make_response
import collections
from ortools.sat.python import cp_model
import jwt
from functools import wraps
import uuid, datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
db = SQLAlchemy(app)

# Class Stored in Database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

app.config['SECRET_KEY'] = 'jobshopkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

simulations = [{'id': 0, 'nmachines': 1, 'njobs': 1, 'nops': 1}]
jobs = []

# Lists all users
@app.route('/user', methods=['GET'])
def get_users():
    users = User.query.all()
    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)
    return jsonify({'Users': output})

# Create new user
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'result': "New User Created!"}), 201

# Change pass of a user
@app.route('/user/<public_id>', methods=['PUT'])
def change_pass(public_id):
    data = request.get_json()
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'Error': "User not found!"}), 404

    user.password = generate_password_hash(data['password'], method='sha256')
    db.session.commit()

    return jsonify({'result': "User Updated!"}), 201

# Deletes a user
@app.route('/user/<public_id>', methods=['DELETE'])
def delete_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'Error': "User not found!"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'result': "User Deleted!"})

# Login
@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login Required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login Required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login Required!"'})

# List all simulations
@app.route("/sims", methods=['GET'])
def list_sims():
    return jsonify({'simulations': simulations})

# Criar new simulation
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
        return jsonify({'result': "Machines, Jobs, Operations must be equal"}), 500

    simulations.append(simulation)
    return jsonify({'simulation': simulation}), 201

# Delete a simulation
@app.route("/deletesim/<int:id_sim>", methods=['DELETE'])
def delete_sim(id_sim):
    simulation = [simulation for simulation in simulations if simulation['id'] == id_sim]
    if len(simulation) == 0:
        return jsonify({'Error': "Simulation not found"}), 404
    simulations.remove(simulation[0])
    return jsonify({'result': True})

# Add Operations in a desired job
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

# Create a new table verifying if all fields are filled
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

# Update table already created
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

# Download process table
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

# Add start time for each operation
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
        
        if (start_time >= sum) and ((start_time < start_work) or (start_time > end_work)):
            op[0]['start_time'] = start_time
            return jsonify({'start_time': start_time}), 201
        else:                
            return jsonify({'Error': "Invalid Start Time"}), 500

# Verify if operations fields are all filled
@app.route("/verifyplan", methods=['GET'])
def verify_plan():
    fault = False
    total = 0
    for x in jobs:          
        for y in x['operations']:    
            total += y['time'] + y['start_time']
            if "start_time" not in y:
                fault = True
    if fault:
        return jsonify({'Error': "Start Time Missing"}), 500
    else:
        return jsonify({'result': "Success, Table Completed!", 'total': total}), 200

# Download process plan
@app.route("/downloadplan", methods=['GET'])
def download_plan():
    f = open("src/plan.txt", "w")

    for i in jobs:
        for y in i['operations']:
            start = y['start_time']
            duration = y['time']
            end = start + duration
            f.write('job(%s) op(%s) machine(%s) start(%s) duration(%s) end(%s)' % ((str)(i['id']), (str)(y['id_op']), (str)(y['machine']),
            (str)(start), (str)(duration), (str)(end)))
            f.write("\n")
    f.close()
    path = "plan.txt"
    return send_file(path, as_attachment=True)

# Find best result in process plan
@app.route("/ortools", methods=['GET'])
def ortools():
    jobs_list = []
    lst_job = []
    start_times = []
    index = 0

    # Convert into list of tuples
    for i in jobs:
        for j in i['operations']:
            lst = (j['machine'], j['time'])
            lst_job.append(lst)
        jobs_list.append(lst_job)
        lst_job = [] 

    jobs_data = jobs_list
    
    machines_count = 1 + max(task[0] for job in jobs_data for task in job)
    all_machines = range(machines_count)
    # Computes horizon dynamically as the sum of all durations.
    horizon = sum(task[1] for job in jobs_data for task in job)

    # Create the model.
    model = cp_model.CpModel()

    # Named tuple to store information about created variables.
    task_type = collections.namedtuple('task_type', 'start end interval')
    # Named tuple to manipulate solution information.
    assigned_task_type = collections.namedtuple('assigned_task_type',
                                                'start job index duration')

    # Creates job intervals and add to the corresponding machine lists.
    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)

    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine = task[0]
            duration = task[1]
            suffix = '_%i_%i' % (job_id, task_id)
            start_var = model.NewIntVar(0, horizon, 'start' + suffix)
            end_var = model.NewIntVar(0, horizon, 'end' + suffix)
            interval_var = model.NewIntervalVar(start_var, duration, end_var,
                                                'interval' + suffix)
            all_tasks[job_id, task_id] = task_type(start=start_var,
                                                   end=end_var,
                                                   interval=interval_var)
            machine_to_intervals[machine].append(interval_var)

    # Create and add disjunctive constraints.
    for machine in all_machines:
        model.AddNoOverlap(machine_to_intervals[machine])

    # Precedences inside a job.
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.Add(all_tasks[job_id, task_id +
                                1].start >= all_tasks[job_id, task_id].end)

    # Makespan objective.
    obj_var = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(obj_var, [
        all_tasks[job_id, len(job) - 1].end
        for job_id, job in enumerate(jobs_data)
    ])
    model.Minimize(obj_var)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print('Solution:')
        # Create one list of assigned tasks per machine.
        assigned_jobs = collections.defaultdict(list)
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                machine = task[0]
                assigned_jobs[machine].append(
                    assigned_task_type(start=solver.Value(
                        all_tasks[job_id, task_id].start),
                                       job=job_id,
                                       index=task_id,
                                       duration=task[1]))

        # Create per machine output lines.
        output = ''
        for machine in all_machines:
            # Sort by starting time.
            assigned_jobs[machine].sort()
            sol_line_tasks = 'Machine ' + str(machine) + ': '
            sol_line = '           '
           
            for assigned_task in assigned_jobs[machine]:
                name = 'job_%i_task_%i' % (assigned_task.job,
                                           assigned_task.index)
                # Add spaces to output to align columns.
                sol_line_tasks += '%-15s' % name

                start = assigned_task.start
                duration = assigned_task.duration
                sol_tmp = '[%i,%i]' % (start, start + duration)
                # Add spaces to output to align columns.
                sol_line += '%-15s' % sol_tmp
                start_times.append(start)

            sol_line += '\n'
            sol_line_tasks += '\n'
            output += sol_line_tasks
            output += sol_line

        # Finally print the solution found.
        print(f'Optimal Schedule Length: {solver.ObjectiveValue()}')
        print(output)
    else:
        return jsonify({'Error': "No Solution Found!"}), 500

    # Add start time for each operation defined by or-tools
    for a in jobs:
        for b in a['operations']:
            b['start_time'] = start_times[index]
            index += 1

    return jsonify({'Finish Time': solver.ObjectiveValue()}), 200

# Download text file with automated plan
@app.route("/downloadauto", methods=['GET'])
def download_auto():
    f = open("src/automated.txt", "w")

    for i in jobs:
        for y in i['operations']:
            start = y['start_time']
            duration = y['time']
            end = start + duration
            f.write('job(%s) op(%s) machine(%s) start(%s) duration(%s) end(%s)' % ((str)(i['id']), (str)(y['id_op']), (str)(y['machine']),
            (str)(start), (str)(duration), (str)(end)))
            f.write("\n")
    f.close()
    path = "automated.txt"
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

