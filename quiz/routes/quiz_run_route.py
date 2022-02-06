from quiz import app, db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *
import random

num_quiz_questions = 10
quiz_question_id_lst = []
quiz_answer_lst = []
quiz_qn_lst = []

# Start the quiz and get questions one-by-one
@app.route('/run-quiz', methods=['GET','POST'])
@login_required # Don't allow to take quiz unless logged-in
def run_quiz():

    oth_form = OtherAnswerForm()  # This form is to accept answer for 'Fill In the Blanks' question-type
    if request.method == 'POST':
        if len(oth_form.oth_answer.data) > 0: # For 'Fill In The Blanks' questions, users response to be considered is 'oth_answer'
            user_response = oth_form.oth_answer.data
        else:
            user_response = request.form['options']  # For all the remaining questions it should be 'options' coming back from form
        quiz_response_lst.append(user_response)
        return redirect(url_for('run_quiz'))

    if quiz_qn_lst:
        for question in quiz_qn_lst:
            if question.question_type == 'Fill-In-The Blank':   # For 'Fill-In-The-Blanks' questions answer will be stored in 'other_answer' column in DB
                quiz_answer_lst.append(question.other_answer)
            else:
                quiz_answer_lst.append(question.answer)
            quiz_question_id_lst.append(str(question.id))
            image_choice_list   = [('A', question.image1),
                                   ('B', question.image2),
                                   ('C', question.image3),
                                   ('D', question.image4),
                                   ('E', question.image5)]
            quiz_qn_lst.remove(question)
            return render_template("quiz_questions.html",
                                   image_choices=image_choice_list,
                                   question=question,
                                   oth_form=oth_form,
                                   )
    else:
        quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, current_user.id)
        flash('Quiz completed successfully !')
        return render_template("quiz_score.html",
                               quiz_score=quiz_score,
                               quiz_total=quiz_total,
                               )

# Start the quiz and get questions one-by-one
@app.route('/start-quiz', methods=['GET','POST'])
def start_quiz():

    if request.method == 'POST':
        questions = Questions.query.order_by(Questions.id)
        quiz_qn_lst_all = []
        for qn in questions:
            if qn.active_flag == 'Active':
                quiz_qn_lst_all.append(qn)
        random.shuffle(quiz_qn_lst_all)
        global quiz_qn_lst
        quiz_qn_lst = quiz_qn_lst_all[:num_quiz_questions]
        #print('len(quiz_qn_lst):',len(quiz_qn_lst), 'len(quiz_qn_lst_all):', len(quiz_qn_lst_all))
        return redirect(url_for('run_quiz'))

    return render_template("start_quiz.html")