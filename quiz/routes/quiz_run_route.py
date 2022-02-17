from quiz import app, db
import time
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *

user_response= ''
quiz_time = 30

# Start the quiz and get questions one-by-one
@app.route('/start-quiz', methods=['GET','POST'])
@login_required # Don't allow to take quiz unless logged-in
def start_quiz():

    global user_response, end, start
    if request.method == 'POST':
        oth_form = OtherAnswerForm()  # This form is to accept answer for 'Fill In the Blank' question-type
        oth_form2 = OtherAnswerForm2() # This form is to accept answer for 'Fill In the BlankS' question-type
        if len(request.form.keys()) > 0:
           if len(oth_form.oth_answer.data) > 0:  # For 'Fill In The Blank' questions, users response to be considered is 'oth_answer'
               user_response = oth_form.oth_answer.data
           elif len(oth_form2.oth_answer1.data) > 0:  # For 'Fill In The BlankS' questions, users response to be considered is 'oth_answer1'
               user_response = oth_form2.oth_answer1.data + '*' + oth_form2.oth_answer2.data
           else:
               user_response = request.form['options']  # For all the remaining questions it should be 'options' coming back from form
           next_qn_id = temp_quiz_db('update-response', user_response)
           end = time.perf_counter()
        else:  # While coming for first time there wont be any data in request.form.keys. Hence fetch qn-id to be displayed for quiz.
           next_qn_id = temp_quiz_db('read-next-qn-id', '')

        if 'end' in globals():
            print('end-start:', end, '|', start, '|', end - start)
        else:
            'end not captured'

        if next_qn_id == 9999:  # Upon end-of questions, next_qn_id will be updated with 9999
            quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, quiz_qn_type_lst = temp_quiz_db('read', '')
            quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, quiz_qn_type_lst,
                                                          current_user.id)
            _ = temp_quiz_db('delete', '')
            flash(f'Quiz completed successfully ! ')
            return render_template("quiz_score.html",
                                    quiz_score=quiz_score,
                                    quiz_total=quiz_total,)
        else:
            start = time.perf_counter()
            question = Questions.query.filter_by(id=next_qn_id).first()
            image_choice_list = [('A', question.image1),
                                 ('B', question.image2),
                                 ('C', question.image3),
                                 ('D', question.image4),
                                 ('E', question.image5)]
            if question.question_type == 'Fill-In-The Blanks':
                oth_form = OtherAnswerForm2()
                oth_form.oth_answer1.data = ''
                oth_form.oth_answer2.data = ''
            else:
                oth_form = OtherAnswerForm()
                oth_form.oth_answer.data = ''

            return render_template("quiz_questions.html",
                                    image_choices=image_choice_list,
                                    question=question,
                                    oth_form=oth_form,)

    elif request.method == 'GET':   # Initial flow reaches here
        _ = temp_quiz_db('delete', '')   # Cleaning-up temp DB record incase if any past records for same user is present
        temp_quiz_db('create', '')  # Creating a temp record with qn IDs to be used in quiz, their answers & 1st qn id
        return render_template("start_quiz.html")

def time_reducer(n):
    def inner(quiz_time):
        return quiz_time - 1
    return inner






