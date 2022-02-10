from quiz import app, db
from PIL import Image
import random, time, os, re
from quiz.routes import *
from quiz.db_models import *
from pandas import read_excel
from collections import namedtuple
import re

num_quiz_questions = 5
qn_answer = ''
quiz_score_lst = []
quiz_possible_score_lst = []
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']
answer_map_dict = {'image1':1, 'image2':2, 'image3':3, 'image4':4, 'image5':5, 'other':'other',
                   'choice1':1, 'choice2':2, 'choice3':3, 'choice4':4, 'choice5':5,
                   'option1':1, 'option2':2, 'option3':3, 'option4':4, 'option5':5}
fb_logic = namedtuple('fb_logic', 'fb_qn fb_qn_if_correct fb_qn_if_wrong')
fb_qn = namedtuple('fb_qn', 'qn_id qn qn_type answers correct_answer')
fb_qn_dict = {}
fb_logic_dict = {}

# Function to save the image as part of adding/editing questions.
def save_image_qn(image_file_list, current_name_list, action):
    image_filename_list = list()
    for idx, image_file in enumerate(image_file_list):
        if image_file is None:
            if action == 'add':
                image_filename_list.append('default.jpg')
            else:
                image_filename_list.append(current_name_list[idx])
        else:
            img = Image.open(image_file)
            img_filename_list = image_file.filename.split('.')
            timestr = time.strftime("%Y%m%d-%H%M%S")
            img_save_name = str(img_filename_list[0]) + '_' + str(timestr) + '.' + img_filename_list[-1]
            image_save_path = os.path.join(app.root_path, 'static/images', img_save_name)
            img = img.resize((200, 200))
            img.save(image_save_path)
            image_filename_list.append(img_save_name)
    return image_filename_list

# Function to extract past quiz attempt details. Used in quiz_logs_route.
def extract_log_details(log, display_type):

    quiz_log_id = int(log.id)
    # Taking 'quiz_details' stored in Quizlogs database, splitting it based on '^' and '|' and populate it to respective lists/variable
    details = log.quiz_details
    string_lst = details.split('^')
    quiz_taker_username = string_lst[0]
    quiz_question_id_lst = string_lst[1].split('|')
    quiz_answer_lst = string_lst[2].split('|')
    quiz_response_lst = string_lst[3].split('|')
    quiz_score_lst = string_lst[4].split('|')
    quiz_possible_score_lst = string_lst[5].split('|')
    quiz_score = string_lst[6]
    quiz_total = string_lst[7]
    quiz_taken_date = str(log.date_taken)[:19]

    quiz_question_display_list = []
    if display_type == 'detailed':
        for idx, qn_id in enumerate(quiz_question_id_lst):
            quiz_qn = Questions.query.filter_by(id=int(qn_id)).first()
            image_choice_list = [('A', quiz_qn.image1),
                                 ('B', quiz_qn.image2),
                                 ('C', quiz_qn.image3),
                                 ('D', quiz_qn.image4),
                                 ('E', quiz_qn.image5)]
            quiz_question_display_list.append((quiz_qn,
                                               quiz_answer_lst[idx],
                                               quiz_response_lst[idx],
                                               quiz_score_lst[idx],
                                               quiz_possible_score_lst[idx],
                                               image_choice_list))
        return (quiz_log_id, quiz_taker_username, quiz_question_display_list, quiz_score, quiz_total, quiz_taken_date)
    else:
        return (quiz_log_id, quiz_taker_username, len(quiz_question_id_lst), quiz_score, quiz_total, quiz_taken_date)

# Function to calculate the quiz score upon attempting all the questions and save the details to Quizlogs DB
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

# Function to prepare feedback questions and control logic based on the response for each feedback question
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

# Function to read/update temp_feedback DB
def temp_fb_db(method, fb_qn, fb_response, fb_qn_id):
    # Creating a record to temp_feedback DB. Initial create below will be having list of qn IDs to be used in quiz, their answers &.
    # next qn id. As quiz progresses, this DB record created below will get updated with responses and next qn id to be shown.
    if method == 'create':

        feedback_taker_id = current_user.id
        fb_temp = Feedbacktemp(fb_qn_str=fb_qn,
                               fb_response_str='',
                               fb_qn_id=fb_qn_id,
                               feedback_taker_id=feedback_taker_id)

        # Add the values to database
        db.session.add(fb_temp)
        db.session.commit()

    # Fetching the feedback-question-id that got already displayed
    elif method == 'read-qn-id':
        fb_temp = Feedbacktemp.query.filter_by(feedback_taker_id=current_user.id).first()

        return fb_temp.fb_qn_id

    # Fetching the question_id_list used in quiz, their corresponding answers and user responses
    elif method == 'read-list':
        fb_temp = Feedbacktemp.query.filter_by(feedback_taker_id=current_user.id).first()

        fb_qn_str = fb_temp.fb_qn_str
        fb_qn_lst = fb_qn_str.split('|')

        fb_response_str = fb_temp.fb_response_str
        fb_response_lst = fb_response_str.split('|')

        return fb_qn_lst, fb_response_lst

    # Updating the response that user provided while taking the feedback and next question ID to be displayed
    elif method == 'update':
        fb_temp = Feedbacktemp.query.filter_by(feedback_taker_id=current_user.id).first()

        fb_temp.fb_qn_id = fb_qn_id
        fb_response_str = fb_temp.fb_response_str
        if fb_response_str == '':  # response_str while creating the temp record was ''.Overwriting it with first response
            fb_response_str = str(fb_response)
        else:
            fb_response_str = fb_response_str + '|' + str(fb_response)
        fb_temp.fb_response_str = fb_response_str

        fb_qn_str = fb_temp.fb_qn_str
        if fb_qn_str == '':  # fb_qn_str while creating the temp record was ''.Overwriting it with first response
            fb_qn_str = str(fb_qn)
        else:
            fb_qn_str = fb_qn_str + '|' + str(fb_qn)
        fb_temp.fb_response_str = fb_response_str
        fb_temp.fb_qn_str = fb_qn_str

        # Updating the database record
        db.session.commit()
        return fb_qn_id

    # Deleting the temp record belonging toe the current user-id
    elif method == 'delete':
        fb_temps = Feedbacktemp.query.filter_by(feedback_taker_id=current_user.id)
        recs_deleted = 0
        for fb_temp in fb_temps:
            db.session.delete(fb_temp)
            db.session.commit()
            recs_deleted += 1
        return recs_deleted

