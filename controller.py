from flask import flash, redirect, render_template, request, url_for
from flask_login import login_user, LoginManager, login_required, logout_user
from flask_bcrypt import Bcrypt
from sqlalchemy import delete
from main import app
from models import *
from schemas import *

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                if user.username == "admin":
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template('admin.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('register.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/sims', methods=['GET', 'POST'])
def sims():
    return render_template('sims.html')

@app.route('/sims/create_sim', methods=['GET', 'POST'])
def create_sim():
    form = SimForm()
    if form.validate_on_submit():
        new_sim = Simulation(nmachines=form.nmachines.data, nworks=form.nworks.data, nops=form.nops.data)
        db.session.add(new_sim)
        db.session.commit()
        return redirect(url_for('sims'))
    return render_template('create_sim.html', form=form)

@app.route('/sims/list_sims', methods=['GET'])
def list_sims():
    sims = Simulation.query.all()
    return render_template('list_sims.html', sims=sims)

@app.route('/sims/delete_sim', methods=['GET', 'POST', 'DELETE'])
def delete_sim():
    form = DeleteSimForm()
    if form.validate_on_submit():
        has_sim = Simulation.query.get_or_404(form.id)
        db.session.delete(has_sim)
        db.session.commit()
        return redirect(url_for('sims'))
    return render_template('delete_sim.html', form=form)