from quiz import app, db
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from quiz.forms import *
from quiz.db_models import *
from flask import Flask, render_template, flash, request, redirect, url_for
from quiz.utils import *
from collections import namedtuple
from sqlalchemy import desc

# Flask login requisites
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

fb_qn_dict = {}
fb_logic_dict = {}
fb_qn_lst = []
fb_response_lst = []

fb_qn_dict, fb_logic_dict = prep_feedback_data()

# This function will provide the next question-id based on the previous question-id and its corresponding response
# Questions are created as named tuples in the format -> namedtuple('fb_qn', 'qn_id qn qn_type answers correct_answer')
# Logics are also created as named tuples in the format -> namedtuple('fb_logic', 'fb_qn fb_qn_if_correct fb_qn_if_wrong')
def control_flow(fb_response, fb_qn_id):
    fb_logic = fb_logic_dict[str(fb_qn_id)]
    fb_qn = fb_qn_dict[str(fb_qn_id)]
    if fb_qn.correct_answer == fb_response:
        return fb_logic.fb_qn_if_correct
    else:
        if fb_logic.fb_qn_if_wrong not in fb_qn_dict:
            return fb_logic.fb_qn_if_correct
        else:
            return fb_logic.fb_qn_if_wrong

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create login page
@app.route('/login', methods=['GET', 'POST'])
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
@app.route('/logout', methods=['GET', 'POST'])
@login_required  # We can't logout unless logged-in
def logout():
    # Upon submission of feedback response, flow will keep coming here
    oth_form = OtherAnswerForm()
    if request.method == 'POST':
        if len(oth_form.oth_answer.data) > 0:  # For 'text' questions, user response may be in form of text
            fb_response = oth_form.oth_answer.data
        else:
            fb_response = request.form['options']
        displayed_fb_qn_id = temp_fb_db('read-qn-id', '', '', '')
        fb_qn_displayed = fb_qn_dict[str(displayed_fb_qn_id)]
        to_be_displayed_qn_id = control_flow(fb_response, displayed_fb_qn_id)
        to_be_displayed_fb_qn = fb_qn_dict[str(to_be_displayed_qn_id)]
        if to_be_displayed_fb_qn.qn_type == 'message':
            temp_fb_db('update', fb_qn_displayed.qn, fb_response, to_be_displayed_qn_id)
            fb_qn_lst, fb_response_lst = temp_fb_db('read-list', '', '', '')
            save_to_feedback_db(fb_qn_lst, fb_response_lst)
            deleted_recs = temp_fb_db('delete', '', '', '')
            logout_user()
            flash(f' {to_be_displayed_fb_qn.qn} - Logged out successfully !')
            return redirect(url_for('login'))
        else:
            temp_fb_db('update', fb_qn_displayed.qn, fb_response, to_be_displayed_qn_id)
            answer_lst = to_be_displayed_fb_qn.answers.split('*')
            if to_be_displayed_fb_qn.qn_type == 'radio-text':
                oth_form.oth_answer.data = 'If Other, please enter details here'
            else:
                oth_form.oth_answer.data = ''
            return render_template("feedback.html",
                                   qn=to_be_displayed_fb_qn,
                                   answer_lst=answer_lst,
                                   oth_form=oth_form)

    # Upon clicking logout, Initial flow will come here
    qn_id = 1
    first_fb_qn = fb_qn_dict[str(qn_id)]
    temp_fb_db('delete', '', '', '')
    temp_fb_db('create', '', '', qn_id)
    answer_lst = first_fb_qn.answers.split('*')
    return render_template("feedback.html",
                           qn=first_fb_qn,
                           answer_lst=answer_lst,
                           oth_form=oth_form)

# Create dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required  # This will help reroute back to login page if not logged-in
def dashboard():
    our_users = Users.query.order_by(Users.date_added)
    return render_template('dashboard.html',
                           our_users=our_users)

# Create route decorator
@app.route('/')
def index():
    message = ' <strong> Welcome...If new user, Please go to Register tab to sign-up </strong>'
    return render_template("index.html",
                           message=message,
                           )

# Show the feedbacks recorded as a list
@app.route('/show_feedbacks', methods=['GET', 'POST'])
@login_required  # Don't allow to see feedbacks unless logged-in
def show_feedbacks():
    feedbacks_lst = []
    if current_user.role == 'admin':
        feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()

        for fb in feedbacks:
            fb_detail = (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
            feedbacks_lst.append(fb_detail)

        return render_template("show_feedbacks.html",
                               feedbacks_lst=feedbacks_lst)

# Delete individual feedbacks
@app.route('/show_feedbacks/delete/<int:id>')  # Pass ID of feedback to be deleted
@login_required  # Dont allow to delete feedback unless logged-in.
def delete_feedback(id):
    feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()
    feedbacks_lst = []
    for fb in feedbacks:
        fb_detail = (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
        feedbacks_lst.append(fb_detail)

    feedback_to_delete = Feedbacks.query.get_or_404(id)
    # Only admin can delete the feedback.
    if current_user.role == 'admin':
        try:
            db.session.delete(feedback_to_delete)
            db.session.commit()
            flash(f'Feedback deleted successfully!')
            feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()
            feedbacks_lst = []
            for fb in feedbacks:
                fb_detail = (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
                feedbacks_lst.append(fb_detail)
            return render_template("show_feedbacks.html",
                                   feedbacks_lst=feedbacks_lst)
        except:
            flash('Couldnt delete feedback !')
            return render_template("show_feedbacks.html",
                                   feedbacks_lst=feedbacks_lst)
    else:
        flash(f'Feedback Cant be deleted. You are not authorized to delete this feedback')
        return render_template("show_feedbacks.html",
                               feedbacks_lst=feedbacks_lst)

