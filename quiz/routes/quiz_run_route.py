from quiz import app, db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *
import random, re

num_quiz_questions = 5
user_response= ''
qn_answer = ''

# Start the quiz and get questions one-by-one
@app.route('/start-quiz', methods=['GET','POST'])
@login_required # Don't allow to take quiz unless logged-in
def start_quiz():

    global user_response
    if request.method == 'POST':
        oth_form = OtherAnswerForm()  # This form is to accept answer for 'Fill In the Blanks' question-type
        if len(request.form.keys()) > 0:
           if len(oth_form.oth_answer.data) > 0:  # For 'Fill In The Blanks' questions, users response to be considered is 'oth_answer'
               user_response = oth_form.oth_answer.data
           else:
               user_response = request.form['options']  # For all the remaining questions it should be 'options' coming back from form
           next_qn_id = temp_quiz_db('update-response', user_response)
        else:
           next_qn_id = temp_quiz_db('read-next-qn-id', '')

        if next_qn_id == 9999:  # Upon end-of questions, next_qn_id will be updated with 9999
            quiz_question_id_lst, quiz_answer_lst, quiz_response_lst = temp_quiz_db('read', '')
            quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst,
                                                          current_user.id)
            _ = temp_quiz_db('delete', '')
            flash(f'Quiz completed successfully ! ')
            return render_template("quiz_score.html",
                                    quiz_score=quiz_score,
                                    quiz_total=quiz_total,)
        else:
            oth_form = OtherAnswerForm()
            question = Questions.query.filter_by(id=next_qn_id).first()
            image_choice_list = [('A', question.image1),
                                 ('B', question.image2),
                                 ('C', question.image3),
                                 ('D', question.image4),
                                 ('E', question.image5)]
            oth_form.oth_answer.data = ''
            return render_template("quiz_questions.html",
                                    image_choices=image_choice_list,
                                    question=question,
                                    oth_form=oth_form,)

    elif request.method == 'GET':   # Initial flow reaches here
        _ = temp_quiz_db('delete', '')   # Cleaning-up temp DB record incase if any past records for same user is present
        temp_quiz_db('create', '')       # Creating a temp record with qn IDs to be used in quiz, their answers & 1st qn id
        return render_template("start_quiz.html")

# Function to read/update temp_quiz DB
def temp_quiz_db(method, response):

    # Creating a record to temp_quiz DB. Initial create below will be having list of qn IDs to be used in quiz, their answers &.
    # next qn id. As quiz progresses, this DB record created below will get updated with responses and next qn id to be shown.
    if method == 'create':

        quiz_qn_list = []
        quiz_qn_id_list = []
        quiz_qn_ans_list = []
        questions = Questions.query.order_by(Questions.id)
        for qn in questions:
            if qn.active_flag == 'Active':
                if qn.question_type == 'Fill-In-The Blank':  # For 'Fill-In-The-Blanks' questions answer will be stored in 'other_answer' column in DB
                    qn_answer = qn.other_answer
                else:
                    qn_answer = qn.answer
                qn_id = qn.id
                tup = (qn_id, qn_answer)
                quiz_qn_list.append(tup)

        random.shuffle(quiz_qn_list)      # Randomly shuffling the questions
        quiz_qn_list = quiz_qn_list[:num_quiz_questions]    # Selecting number of questions to be used in the quiz

        # Preparing string of question Ids, their answers and ID of first qn to be displayed in the quiz.
        for qn_id, ans in quiz_qn_list:
            quiz_qn_id_list.append(qn_id)
            quiz_qn_ans_list.append(ans)
        qn_id_str = "|".join(map(str, quiz_qn_id_list))
        next_qn_id = quiz_qn_id_list[0]
        answer_str = "|".join(quiz_qn_ans_list)

        quiz_taker_id = current_user.id
        quiz_temp = Quiztemp(qn_id_str = qn_id_str,
                             answer_str= answer_str,
                             response_str='',
                             next_qn_id=next_qn_id,
                             quiz_taker_id = quiz_taker_id)

        # Add the values to database
        db.session.add(quiz_temp)
        db.session.commit()

    # Fetching the next-question-id to be shown in the quiz
    elif method == 'read-next-qn-id':
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        return quiz_temp.next_qn_id

    # Fetching the question_id_list used in quiz, their corresponding answers and user responses
    elif method == 'read':
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        qn_id_str = quiz_temp.qn_id_str
        qn_id_lst = qn_id_str.split('|')

        answer_str = quiz_temp.answer_str
        answer_lst = answer_str.split('|')

        response_str = quiz_temp.response_str
        response_lst = response_str.split('|')

        return qn_id_lst, answer_lst, response_lst

    # Updating the response that user provided while taking the quiz and next question ID to be displayed
    elif method == 'update-response':
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        # Fetching next qn ID to be displayed
        current_qn_id = str(quiz_temp.next_qn_id)
        qn_id_str = quiz_temp.qn_id_str
        qn_id_lst = qn_id_str.split('|')
        idx = qn_id_lst.index(current_qn_id)
        if (idx+1) < len(qn_id_lst):
            next_qn_id = int(qn_id_lst[idx+1])
        else:
            next_qn_id = 9999
        quiz_temp.next_qn_id = next_qn_id

        response_str = quiz_temp.response_str
        if response_str == '':   # response_str while creating the temp record was ''.Overwriting it with first response
            response_str = str(response)
        else:
            response_str = response_str + '|' + str(response)
        quiz_temp.response_str = response_str

        # Updating the database record
        db.session.commit()
        return next_qn_id

    # Deleting the temp record belonging toe the current user-id
    elif method == 'delete':
        quiz_temps = Quiztemp.query.filter_by(quiz_taker_id=current_user.id)
        recs_deleted = 0
        for quiz_temp in quiz_temps:
            db.session.delete(quiz_temp)
            db.session.commit()
            recs_deleted += 1
        return recs_deleted





