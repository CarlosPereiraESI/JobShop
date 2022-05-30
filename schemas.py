from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError, NumberRange
from models import *

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")

    def valid_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("User already exists!")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

class SimForm(FlaskForm):
    nmachines = IntegerField('Number of Machines', [InputRequired(), NumberRange(min=1, max=99, message="Invalid range")])
    nworks = IntegerField('Number of Works', [InputRequired(), NumberRange(min=1, max=99, message="Invalid range")])
    nops = IntegerField('Number of Operations', [InputRequired(), NumberRange(min=1, max=99, message="Invalid range")])
    submit = SubmitField("Create")

class DeleteSimForm(FlaskForm):
    id = IntegerField('Simulation ID', [InputRequired(), NumberRange(min=1, max=99, message="Invalid range")])
    submit = SubmitField("Delete")