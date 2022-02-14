from quiz import app, db
from PIL import Image
import random, time, os, re
from quiz.routes import *
from quiz.db_models import *
from pandas import read_excel
from collections import namedtuple
import re
from flask_login import login_required, current_user
from fractions import Fraction

num_quiz_questions = 6
qn_answer = ''
quiz_score_lst = []
quiz_possible_score_lst = []
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']
answer_map_dict = {'image1':1, 'image2':2, 'image3':3, 'image4':4, 'image5':5, 'other':'other',
                   'choice1':1, 'choice2':2, 'choice3':3, 'choice4':4, 'choice5':5,
                   'option1':1, 'option2':2, 'option3':3, 'option4':4, 'option5':5}
regex = re.compile(r'[\n\r\t]')
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
    quiz_response_lst = string_lst[2].split('|')
    quiz_answer_lst = string_lst[3].split('|')
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
def calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst, quiz_qn_type_lst, user_id):
    score = 0
    total = 0

    for i in range(len(quiz_response_lst)):
        answer = ''
        response = ''
        if quiz_answer_lst[i] in answer_types:
            answer = answer_map_dict[quiz_answer_lst[i]]
            response = answer_map_dict[quiz_response_lst[i]]
            quiz_answer_lst[i] = 'Option-' + str(answer)
            quiz_response_lst[i] = 'Option-' + str(response)
        else:     # Answer will be a text response for Fill In The Blank/s and numeric type of questions
            if '*' in quiz_answer_lst[i]:   # Handling Fill In The Blanks
                ans_lst = quiz_answer_lst[i].split('*')
                ans1 = ans_lst[0]
                ans2 = ans_lst[1]
                non_html_ans1 = remove_html_tags(ans1)
                non_html_ans2 = remove_html_tags(ans2)
                answer1 = "".join(non_html_ans1.split()).lower()
                answer2 = "".join(non_html_ans2.split()).lower()
                answer = answer1 + '*' + answer2

                res_lst = quiz_response_lst[i].split('*')
                res1 = res_lst[0]
                res2 = res_lst[1]
                response1 = "".join(res1.split()).lower()
                response2 = "".join(res2.split()).lower()
                response = response1 + '*' + response2

                quiz_answer_lst[i] = answer # Replacing the answer retrieved from DB after removing html tags, spaces & making everything lower cases
                quiz_response_lst[i] = response # Replacing the response from Quiz portal after removing spaces & making everything lower case
            else:        # Handling Fill In The Blank
                if quiz_qn_type_lst[i] != 'numeric':
                    non_html_answer = remove_html_tags(quiz_answer_lst[i])
                    answer = "".join(non_html_answer.split()).lower()
                    response = "".join(quiz_response_lst[i].split()).lower()  # eg : 'aBc d' quiz_response_lst[i].split() -> ['aBc','d']
                                                                              # "".join(quiz_response_lst[i].split()) -> 'aBcd'
                                                                              # "".join(quiz_response_lst[i].split()).lower() -> 'abcd'
                    quiz_answer_lst[i] = answer # Replacing the answer retrieved from DB after removing html tags, spaces & making everything lower cases
                    quiz_response_lst[i] = response # Replacing the response from Quiz portal after removing spaces & making everything lower case

        if quiz_qn_type_lst[i] == 'numeric':  # Handling numeric questions
            non_html_answer = remove_html_tags(quiz_answer_lst[i])
            non_html_answer = "".join(non_html_answer.split()).lower()
            answer = round(float(non_html_answer), 2)

            numeric_response = quiz_response_lst[i]
            non_html_response = remove_html_tags(numeric_response)
            non_space_response = regex.sub("", non_html_response).strip()

            if '/' in non_space_response:
                numeric_response_lst = non_space_response.split('/')
                if len(numeric_response_lst) != 2:
                    response = 'Not-a-numeric-response'
                else:
                    for idx, num_str in enumerate(numeric_response_lst):
                        if num_str.strip().isnumeric():
                            numeric_response_lst[idx] = int(num_str.strip())
                        else:
                            response = 'Not-a-numeric-response'
                            break
                    if response != "Not-a-numeric-response":
                        response = round(float(Fraction(numeric_response_lst[0], numeric_response_lst[1])), 2)
            elif '.' in non_space_response:
                numeric_response_lst = non_space_response.split('.')
                if len(numeric_response_lst) != 2:
                    response = 'Not-a-numeric-response'
                else:
                    for num_str in numeric_response_lst:
                        if num_str.isnumeric():
                            pass
                        else:
                            response = 'Not-a-numeric-response'
                            break
                    if response != 'Not-a-numeric-response':
                        response = round(float(non_space_response), 2)
            else:
                if non_space_response.isnumeric():
                    response = round(float(non_space_response), 2)
                else:
                    response = 'Not-a-numeric-response'

            quiz_answer_lst[i] = str(answer)
            if type(response) is float or type(response) is int:
                quiz_response_lst[i] = numeric_response + ' (Note: Response rounded to 2 decimal places - ' + str(response) + ' )'
            else:
                quiz_response_lst[i] = numeric_response

        if '*' in str(answer):   # For Fill-in-the-BlankS
            quiz_score_temp = 0
            if answer1 == response1:
                quiz_score_temp +=1
                score += 1

            if answer2 == response2:
                quiz_score_temp += 1
                score += 1

            quiz_score_lst.append(str(quiz_score_temp))
            total += 2
            quiz_possible_score_lst.append(str(2))
        else:            # For Fill-in-the-Blank & other questions
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
        quiz_qn_type_list = []
        questions = Questions.query.order_by(Questions.id)
        for qn in questions:
            if qn.active_flag == 'Active':
                if qn.question_type == 'Fill-In-The Blank':  # For 'Fill-In-The-Blank' questions answer will be stored in 'other_answer1' column in DB
                    qn_answer = qn.other_answer1
                elif qn.question_type == 'numeric':  # For 'numeric' questions answer will be stored in 'other_answer1' column in DB
                    qn_answer = qn.other_answer1
                elif qn.question_type == 'Fill-In-The Blanks':  # For 'Fill-In-The-Blanks' questions answer will be stored in 'other_answer1' & 'other_answer2' columns in DB
                    qn_answer = qn.other_answer1 + '*' + qn.other_answer2
                else:
                    qn_answer = qn.answer
                qn_id = qn.id
                qn_type = qn.question_type
                tup = (qn_id, qn_answer, qn_type)
                quiz_qn_list.append(tup)

        random.shuffle(quiz_qn_list)      # Randomly shuffling the questions
        quiz_qn_list = quiz_qn_list[:num_quiz_questions]    # Selecting number of questions to be used in the quiz

        # Preparing string of question Ids, their answers and ID of first qn to be displayed in the quiz.
        for qn_id, ans, qn_type in quiz_qn_list:
            quiz_qn_id_list.append(qn_id)
            quiz_qn_ans_list.append(ans)
            quiz_qn_type_list.append(qn_type)
        qn_id_str = "|".join(map(str, quiz_qn_id_list))
        next_qn_id = quiz_qn_id_list[0]
        answer_str = "|".join(quiz_qn_ans_list)
        qn_type_str = "|".join(quiz_qn_type_list)

        quiz_taker_id = current_user.id
        quiz_temp = Quiztemp(qn_id_str = qn_id_str,
                             answer_str= answer_str,
                             response_str='',
                             qn_type_str=qn_type_str,
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

        qn_type_str = quiz_temp.qn_type_str
        qn_type_lst = qn_type_str.split('|')

        return qn_id_lst, answer_lst, response_lst, qn_type_lst

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

# Saving the details to Feedback DB before logout
def save_to_feedback_db(fb_qn_lst, fb_response_lst):
    feedback_db_str = ''
    for i in range(len(fb_response_lst)):
        feedback_db_str += str(fb_qn_lst[i]) + '|' + str(fb_response_lst[i]) + '|'

    feedback_details = feedback_db_str

    feedbacks = Feedbacks(feedback_details=feedback_details,
                          feedback_giver_name=current_user.username)

    db.session.add(feedbacks)
    db.session.commit()
    fb_qn_lst.clear()
    fb_response_lst.clear()

# Create a string separated by '|' for the question supplied in format - id|question|choice1|....
def create_qn_string(var_dict, qn_var_names, sep):
     qn_string = ''
     for qn_key in qn_var_names:
         if qn_key == 'id':
             qn_string = str(var_dict[qn_key])
         else:
             qn_element_non_html = remove_html_tags(str(var_dict[qn_key]))  # Removes html tag
             qn_element_strip = regex.sub("", qn_element_non_html).strip()  # Removes \n\r\t
             qn_string += sep
             qn_string += qn_element_strip
     return qn_string

# Create a list with questions which will be written to 'questions.txt' file. This file will be downloaded by the user
def create_qn_file_list():
    qn_download_list = []
    sep = '|'
    qn_var_names = ['id', 'question', 'question_type','question_category',
                    'choice1', 'choice2', 'choice3', 'choice4', 'choice5',
                    'image1', 'image2', 'image3', 'image4', 'image5',
                    'answer', 'other_answer1', 'other_answer2','active_flag','date_added','qn_creator_id']
    questions = Questions.query.order_by(Questions.id)

    for qn in questions:
        var_dict = vars(qn)
        qn_string = create_qn_string(var_dict, qn_var_names, sep)
        qn_download_list.append(qn_string)
    return qn_download_list

# Function to save the file as part of upload questions.
def save_qn_file(upload_file):

    user_name = current_user.username
    timestr = time.strftime("%Y%m%d")
    file_save_name = str('Uploaded_questions_' + str(user_name) + '_' + str(timestr) + '.txt')
    upload_file_save_path = os.path.join(app.root_path, 'static/files', file_save_name)
    upload_file.save(upload_file_save_path)
    return upload_file_save_path




