from quiz import app, db
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from quiz.forms import *
from quiz.db_models import *
from flask import Flask, render_template, flash, request, redirect, url_for
from quiz.utils import *

# Flask login requisites
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create login page
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hashed password
            if check_password_hash(user.password_hash, form.password.data):
                # form.password.data -> user supplied pwd, user.password_hash -> hashed pwd stored in DB for this username
                # if both these matches , then login successful
                login_user(user)
                flash('Login successful !')
                return redirect(url_for('dashboard'))
            else:
                flash('Password incorrect - please give correct password')
        else:
            flash('Username - doesnt exist. Please try again with correct username')

    return render_template('login.html', form=form)

# Create logout page
@app.route('/logout',methods=['GET','POST'])
@login_required # We can't logout unless logged-in
def logout():
    # Upon submission of feedback response, flow will keep coming here
    oth_form = OtherAnswerForm()
    if request.method == 'POST':
        if len(oth_form.oth_answer.data) > 0: # For 'text' questions, user response may be in form of text
            fb_response = oth_form.oth_answer.data
        else:
            fb_response = request.form['options']
        fb_response_lst.append(fb_response)
        next_qn_id = control_flow(fb_response, fb_qn_lst[-1].qn_id)
        next_fb_qn = fb_qn_dict[str(next_qn_id)]
        if next_fb_qn.qn_type == 'message':
            save_to_feedback_db(fb_qn_lst, fb_response_lst)
            logout_user()
            flash(f' {next_fb_qn.qn} - Logged out successfully')
            return redirect(url_for('login'))
        else:
            fb_qn_lst.append(next_fb_qn)
            answer_lst = next_fb_qn.answers.split('*')
            if next_fb_qn.qn_type == 'radio-text':
                oth_form.oth_answer.data = 'If Other, please enter details here'
            else:
                oth_form.oth_answer.data = ''
            return render_template("feedback.html",
                                    qn=fb_qn_lst[-1],
                                    answer_lst = answer_lst,
                                    oth_form = oth_form)

    # Upon clicking logout, Initial flow will come here
    qn_id = 1
    first_fb_qn = fb_qn_dict[str(qn_id)]
    fb_qn_lst.append(first_fb_qn)
    answer_lst = first_fb_qn.answers.split('*')
    return render_template("feedback.html",
                           qn = fb_qn_lst[-1],
                           answer_lst = answer_lst,
                           oth_form = oth_form)

# Create dashboard page
@app.route('/dashboard',methods=['GET','POST'])
@login_required  # This will help reroute back to login page if not logged-in
def dashboard():
    our_users = Users.query.order_by(Users.date_added)
    return render_template('dashboard.html',
                           our_users=our_users)

#Create route decorator
@app.route('/')
def index():
    message = ' <strong> Welcome...If new user, Please go to Register tab to sign-up </strong>'
    return render_template("index.html",
                           message = message,
                           )