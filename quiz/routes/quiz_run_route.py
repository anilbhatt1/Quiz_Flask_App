from quiz import app, db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *
import random, re

quiz_index_dict = {'num_quiz_questions':5}
num_quiz_questions = 5
quiz_question_id_lst = []
quiz_answer_lst = []
quiz_qn_lst = []
quiz_response_lst = []
quiz_score_lst = []
quiz_possible_score_lst = []
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']
answer_map_dict = {'image1':1, 'image2':2, 'image3':3, 'image4':4, 'image5':5, 'other':'other',
                   'choice1':1, 'choice2':2, 'choice3':3, 'choice4':4, 'choice5':5,
                   'option1':1, 'option2':2, 'option3':3, 'option4':4, 'option5':5}

# Start the quiz and get questions one-by-one
@app.route('/start-quiz', methods=['GET','POST'])
@login_required # Don't allow to take quiz unless logged-in
def start_quiz():

    global quiz_qn_lst
    print('start-quiz:', request.method)
    if request.method == 'POST':
        print('start-quiz:', len(quiz_qn_lst))

        oth_form = OtherAnswerForm()  # This form is to accept answer for 'Fill In the Blanks' question-type
        if len(request.form.keys()) > 0:
           if len(oth_form.oth_answer.data) > 0:  # For 'Fill In The Blanks' questions, users response to be considered is 'oth_answer'
               user_response = oth_form.oth_answer.data
           else:
               user_response = request.form['options']  # For all the remaining questions it should be 'options' coming back from form
           quiz_response_lst.append(user_response)

        if len(quiz_qn_lst) > 0:
            oth_form = OtherAnswerForm()
            question = quiz_qn_lst[0]
            if question.question_type == 'Fill-In-The Blank':  # For 'Fill-In-The-Blanks' questions answer will be stored in 'other_answer' column in DB
                quiz_answer_lst.append(question.other_answer)
            else:
                quiz_answer_lst.append(question.answer)
            quiz_question_id_lst.append(str(question.id))
            image_choice_list = [('A', question.image1),
                                 ('B', question.image2),
                                 ('C', question.image3),
                                 ('D', question.image4),
                                 ('E', question.image5)]
            oth_form.oth_answer.data = ''
            quiz_qn_lst.pop(0)
            return render_template("quiz_questions.html",
                                    image_choices=image_choice_list,
                                    question=question,
                                    oth_form=oth_form,)

        else:
            quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst,
                                                          current_user.id)
            flash('Quiz completed successfully !')
            return render_template("quiz_score.html",
                                    quiz_score=quiz_score,
                                    quiz_total=quiz_total,)

    elif request.method == 'GET':
        questions = Questions.query.order_by(Questions.id)
        quiz_qn_lst = []
        for qn in questions:
            if qn.active_flag == 'Active':
                quiz_qn_lst.append(qn)
        random.shuffle(quiz_qn_lst)
        quiz_qn_lst = quiz_qn_lst[:num_quiz_questions]
        print('show html:', len(quiz_qn_lst), quiz_qn_lst[0])
        return render_template("start_quiz.html")

def calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, user_id):
    score = 0
    total = 0
    for i in range(len(quiz_response_lst)):
        if quiz_answer_lst[i] in answer_types:
            answer = answer_map_dict[quiz_answer_lst[i]]
            response = answer_map_dict[quiz_response_lst[i]]
            quiz_answer_lst[i] = 'Option-' + str(answer)
            quiz_response_lst[i] = 'Option-' + str(response)
        else:     # Answer will be a text response for Fill In The Blanks questions
            non_html_answer = remove_html_tags(quiz_answer_lst[i])
            answer = "".join(non_html_answer.split()).lower()
            response = "".join(quiz_response_lst[i].split()).lower()  # eg : 'aBc d' quiz_response_lst[i].split() -> ['aBc','d']
                                                                      # "".join(quiz_response_lst[i].split()) -> 'aBcd'
                                                                      # "".join(quiz_response_lst[i].split()).lower() -> 'abcd'
            quiz_answer_lst[i] = answer # Replacing the answer retrieved from DB after removing html tags, spaces & making everything lower cases
            quiz_response_lst[i] = response # Replacing the response from Quiz portal after removing spaces & making everything lower case
        if answer == response:
            quiz_score_lst.append(str(1))
            score += 1
        else:
            quiz_score_lst.append(str(0))
        total += 1
        quiz_possible_score_lst.append(str(1))

    quiz_details = current_user.username + '^' + \
                   "|".join(quiz_question_id_lst) + '^' + \
                   "|".join(quiz_answer_lst) + '^' + \
                   "|".join(quiz_response_lst) + '^' + \
                   "|".join(quiz_score_lst) + '^' + \
                   "|".join(quiz_possible_score_lst) + '^' + \
                   str(score) + '^' + \
                   str(total)

    quizlogs = Quizlogs(quiz_details=quiz_details,
                        quiz_taker_id=user_id)

    db.session.add(quizlogs)
    db.session.commit()

    quiz_question_id_lst.clear()
    quiz_answer_lst.clear()
    quiz_response_lst.clear()
    quiz_score_lst.clear()
    quiz_possible_score_lst.clear()
    return score, total

# Function to remove html tags from a string
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)