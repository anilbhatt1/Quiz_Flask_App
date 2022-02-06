from quiz import app, db
from PIL import Image
import time, os, re
from quiz.routes import *
from quiz.db_models import *

# Function to save the image as part of questions
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

# Function to extract log details
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

