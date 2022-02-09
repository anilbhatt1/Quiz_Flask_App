from quiz import app, db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *
import random, re

num_quiz_questions = 5
quiz_score_lst = []
quiz_possible_score_lst = []
user_response= ''
qn_answer = ''
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']
answer_map_dict = {'image1':1, 'image2':2, 'image3':3, 'image4':4, 'image5':5, 'other':'other',
                   'choice1':1, 'choice2':2, 'choice3':3, 'choice4':4, 'choice5':5,
                   'option1':1, 'option2':2, 'option3':3, 'option4':4, 'option5':5}

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
           next_qn_id = temp_quiz_db('update-response', '', user_response)
           print('next_qn_id 1:', next_qn_id)
        else:
           next_qn_id = temp_quiz_db('read-next-qn-id', '', '')
           print('next_qn_id 2:', next_qn_id)

        if next_qn_id == 9999:
            quiz_question_id_lst, quiz_answer_lst, quiz_response_lst = temp_quiz_db('read', '', '')
            quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst,
                                                          current_user.id)
            recs_deleted = temp_quiz_db('delete', '', '')
            flash(f'Quiz completed successfully ! {recs_deleted} temp records cleared')
            return render_template("quiz_score.html",
                                    quiz_score=quiz_score,
                                    quiz_total=quiz_total,)
        else:
            oth_form = OtherAnswerForm()
            print('next_qn_id 3:', next_qn_id)
            question = Questions.query.filter_by(id=next_qn_id).first()
            if question.question_type == 'Fill-In-The Blank':  # For 'Fill-In-The-Blanks' questions answer will be stored in 'other_answer' column in DB
                qn_answer = question.other_answer
            else:
                qn_answer = question.answer
            image_choice_list = [('A', question.image1),
                                 ('B', question.image2),
                                 ('C', question.image3),
                                 ('D', question.image4),
                                 ('E', question.image5)]
            oth_form.oth_answer.data = ''
            temp_quiz_db('update-answer', qn_answer, '')
            return render_template("quiz_questions.html",
                                    image_choices=image_choice_list,
                                    question=question,
                                    oth_form=oth_form,)

    elif request.method == 'GET':
        deleted_records = temp_quiz_db('delete', '', '')
        temp_quiz_db('create', '', '')
        return render_template("start_quiz.html")

# Function to read/update temp_quiz DB
def temp_quiz_db(method, answer, response):

    if method == 'create':
        print('Entering create')
        quiz_qn_list = []
        questions = Questions.query.order_by(Questions.id)
        for qn in questions:
            if qn.active_flag == 'Active':
                quiz_qn_list.append(qn.id)
        random.shuffle(quiz_qn_list)
        quiz_qn_list = quiz_qn_list[:num_quiz_questions]
        qn_id_str = "|".join(map(str, quiz_qn_list))
        next_qn_id = quiz_qn_list[0]
        quiz_taker_id = current_user.id
        quiz_temp = Quiztemp(qn_id_str = qn_id_str,
                             answer_str= '',
                             response_str='',
                             next_qn_id=next_qn_id,
                             quiz_taker_id = quiz_taker_id)
        # Add the values to database
        db.session.add(quiz_temp)
        db.session.commit()

    elif method == 'read-next-qn-id':
        print('Entering read-next-qn-id')
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        return quiz_temp.next_qn_id

    elif method == 'read':
        print('Entering read')
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        qn_id_str = quiz_temp.qn_id_str
        qn_id_lst = qn_id_str.split('|')

        answer_str = quiz_temp.answer_str
        answer_lst = answer_str.split('|')

        response_str = quiz_temp.response_str
        response_lst = response_str.split('|')

        return qn_id_lst, answer_lst, response_lst

    elif method == 'update-answer':
        print('Entering update-answer')
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        #current_qn_id = quiz_temp.next_qn_id
        #qn_id_str = quiz_temp.qn_id_str
        #next_qn_id = quiz_temp.next_qn_id

        answer_str = quiz_temp.answer_str
        if answer_str == '':
            answer_str = str(answer)
        else:
            answer_str = answer_str + '|' + str(answer)
        quiz_temp.answer_str = answer_str

        #response_str = quiz_temp.response_str
        #response_str = response_str + '|' + str(response)

        #quiz_taker_id = current_user.id

        #quiz_temp = Quiztemp(qn_id_str = qn_id_str,
        #                     answer_str= answer_str,
        #                     response_str=response_str,
        #                     next_qn_id=next_qn_id,
        #                     quiz_taker_id = quiz_taker_id)
        # Update the values to database
        #db.session.add(quiz_temp)
        db.session.commit()


    elif method == 'update-response':
        print('Entering update-response')
        quiz_temp = Quiztemp.query.filter_by(quiz_taker_id=current_user.id).first()

        current_qn_id = str(quiz_temp.next_qn_id)
        print('current_qn_id:',current_qn_id)
        qn_id_str = quiz_temp.qn_id_str
        qn_id_lst = qn_id_str.split('|')
        print('qn_id_lst :',qn_id_lst)
        idx = qn_id_lst.index(current_qn_id)
        print('qn_id_lst :', qn_id_lst, 'idx:', idx)
        if (idx+1) < len(qn_id_lst):
            next_qn_id = int(qn_id_lst[idx+1])
            print('next_qn_id in response 1:', next_qn_id)
        else:
            next_qn_id = 9999
        quiz_temp.next_qn_id = next_qn_id

        #answer_str = quiz_temp.answer_str
        #answer_str = answer_str + '|' + str(answer)

        response_str = quiz_temp.response_str
        if response_str == '':
            response_str = str(response)
        else:
            response_str = response_str + '|' + str(response)
        quiz_temp.response_str = response_str

        #quiz_taker_id = current_user.id

        #quiz_temp = Quiztemp(qn_id_str = qn_id_str,
        #                     answer_str= answer_str,
        #                     response_str=response_str,
        #                     next_qn_id=next_qn_id,
        #                     quiz_taker_id = quiz_taker_id)
        # Update the values to database
        #db.session.add(quiz_temp)
        db.session.commit()
        print('next_qn_id in response 2:', next_qn_id)
        return next_qn_id

    elif method == 'delete':
        print('Entering delete')
        quiz_temps = Quiztemp.query.filter_by(quiz_taker_id=current_user.id)
        recs_deleted = 0
        for quiz_temp in quiz_temps:
            db.session.delete(quiz_temp)
            db.session.commit()
            recs_deleted += 1
        print('recs_deleted:', recs_deleted)
        return recs_deleted

def calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, user_id):
    print('len(quiz_answer_lst):',len(quiz_answer_lst), quiz_answer_lst)
    print('len(quiz_response_lst):', len(quiz_response_lst), quiz_response_lst)
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



