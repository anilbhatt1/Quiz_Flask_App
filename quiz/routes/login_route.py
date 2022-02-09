from quiz import app, db
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from quiz.forms import *
from quiz.db_models import *
from flask import Flask, render_template, flash, request, redirect, url_for
from quiz.utils import *
from pandas import read_excel
from collections import namedtuple
import re
from sqlalchemy import desc

# Flask login requisites
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

fb_logic = namedtuple('fb_logic', 'fb_qn fb_qn_if_correct fb_qn_if_wrong')
fb_qn = namedtuple('fb_qn', 'qn_id qn qn_type answers correct_answer')
fb_qn_dict = {}
fb_logic_dict = {}
fb_qn_lst = []
fb_response_lst = []

def prep_feedback_data():
    with open('./feedback_template/fb_qn_statement.txt') as f:
        fb_qn_statement_lst = f.readlines()

    '''
    Preparing feedback questions and storing it in a dictionary in below format
    '1': fb_qn(qn_id=1, qn='Would like to give us a feedback on your experience while using this app ?', qn_type='radio',
             answers='Yes *Not now', correct_answer='Yes')
    '''
    fb_qn_dict = {}
    regex = re.compile(r'[\n\r\t]')
    for statement in fb_qn_statement_lst:
        qn_lst = statement.split('|')
        qn_id_ = qn_lst[0]
        qn_ = regex.sub("", qn_lst[1]).strip()  # Remove \n,\r,\t, leading & trailing spaces
        answers_ = regex.sub("", qn_lst[2]).strip()
        qn_type_ = regex.sub("", qn_lst[3]).strip()
        correct_answer_ = regex.sub("", qn_lst[4]).strip()
        fb_qn_ = fb_qn(qn_id=qn_id_, qn=qn_, qn_type=qn_type_, answers=answers_, correct_answer=correct_answer_)
        fb_qn_dict[qn_id_] = fb_qn_

    '''
    Preparing feedback logics and storing it in a dictionary in below format
    1 : fb_logic(logic_id=1, fb_qn=1, fb_qn_if_correct=2, fb_qn_if_wrong=7)
    '''
    fb_qn_logic_path = './feedback_template/fb_qn_logic.xlsx'
    my_sheet = 'Sheet1'
    df = read_excel(fb_qn_logic_path, sheet_name=my_sheet)
    fb_logic = namedtuple('fb_logic', 'logic_id fb_qn fb_qn_if_correct fb_qn_if_wrong')
    fb_logic_dict = {}

    for i in range(df.shape[0]):
        fb_qn_ = int(df.iloc[i]['Qn'])
        logic_id_ = str(fb_qn_)
        fb_qn_if_correct_ = str(df.iloc[i]['Correct'])
        fb_qn_if_wrong_ = str(df.iloc[i]['Incorrect'])
        fb_logic_dict[logic_id_] = fb_logic(logic_id=logic_id_, fb_qn=fb_qn_, fb_qn_if_correct=fb_qn_if_correct_,
                                            fb_qn_if_wrong=fb_qn_if_wrong_)

    return fb_qn_dict, fb_logic_dict

fb_qn_dict, fb_logic_dict = prep_feedback_data()

def control_flow(fb_response, fb_qn_id):
    print('fb_logic_dict.keys() inside control_flow:', fb_logic_dict.keys())
    print('fb_qn_dict.keys() inside control_flow:', fb_qn_dict.keys())
    fb_logic = fb_logic_dict[str(fb_qn_id)]
    fb_qn = fb_qn_dict[str(fb_qn_id)]
    if fb_qn.correct_answer == fb_response:
        return fb_logic.fb_qn_if_correct
    else:
        if fb_logic.fb_qn_if_wrong not in fb_qn_dict:
            return fb_logic.fb_qn_if_correct
        else:
            return fb_logic.fb_qn_if_wrong

def make_display_list(qn_id):
    fb_qn = fb_qn_dict[qn_id]
    qn_lst_temp = fb_qn.qn.split('|')
    qn_type_lst_temp = fb_qn.qn_type.split('|')
    ans_lst_temp = fb_qn.answers.split('|')
    qn_ans_lst_temp = list(zip(qn_lst_temp, qn_type_lst_temp, ans_lst_temp))
    display_lst = list()
    for quest, quest_type, ans in qn_ans_lst_temp:
        tup = (quest, quest_type, ans.split('*'))
        display_lst.append(tup)
    return display_lst, fb_qn

# Saving the details to Feedback DB before logout
def save_to_feedback_db(fb_qn_lst, fb_response_lst):

    feedback_db_str = ''
    for i in range(len(fb_response_lst)):
        q_id = fb_qn_lst[i].qn_id
        feedback_db_str += str(q_id) + '|' + str(fb_response_lst[i]) +'|'

    feedback_details = feedback_db_str

    feedbacks =Feedbacks(feedback_details=feedback_details,
                         feedback_giver_name=current_user.username)

    db.session.add(feedbacks)
    db.session.commit()
    fb_qn_lst.clear()
    fb_response_lst.clear()

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
        fb_response_lst.append(fb_response)  # Use DB to save this
        print('fb_qn_dict.keys() After control_flow to get next question:', fb_qn_dict.keys())
        next_qn_id = control_flow(fb_response, fb_qn_lst[-1].qn_id)
        next_fb_qn = fb_qn_dict[str(next_qn_id)]
        if next_fb_qn.qn_type == 'message':
            save_to_feedback_db(fb_qn_lst, fb_response_lst)
            logout_user()
            flash(f' {next_fb_qn.qn} - Logged out successfully')
            return redirect(url_for('login'))
        else:
            print('fb_qn_dict.keys() on way to display feedback.html:', fb_qn_dict.keys())
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
    print('fb_qn_dict.keys() Initial Flow:', fb_qn_dict.keys())
    fb_qn_lst.append(first_fb_qn) # Use DB to save this
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

# Show the feedbacks recorded as a list
@app.route('/show_feedbacks', methods=['GET','POST'])
@login_required # Don't allow to see feedbacks unless logged-in
def show_feedbacks():

    feedbacks_lst = []
    if current_user.role == 'admin':
        feedbacks =Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()

        for fb in feedbacks:
            fb_detail =  (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
            feedbacks_lst.append(fb_detail)

        return render_template("show_feedbacks.html",
                               feedbacks_lst =feedbacks_lst)

# Delete individual feedbacks
@app.route('/show_feedbacks/delete/<int:id>') # Pass ID of feedback to be deleted
@login_required #Dont allow to delete feedback unless logged-in.
def delete_feedback(id):
    feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()
    feedbacks_lst = []
    for fb in feedbacks:
        fb_detail =  (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
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
                                   feedbacks_lst =feedbacks_lst)
        except:
            flash('Couldnt delete feedback !')
            return render_template("show_feedbacks.html",
                                   feedbacks_lst =feedbacks_lst)
    else:
        flash(f'Feedback Cant be deleted. You are not authorized to delete this feedback')
        return render_template("show_feedbacks.html",
                               feedbacks_lst =feedbacks_lst)