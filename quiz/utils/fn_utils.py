from quiz import app, db
from PIL import Image
import time, os, re
from quiz.routes import *
from quiz.db_models import *

quiz_score_lst = []
quiz_possible_score_lst = []
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']
answer_map_dict = {'image1':1, 'image2':2, 'image3':3, 'image4':4, 'image5':5, 'other':'other',
                   'choice1':1, 'choice2':2, 'choice3':3, 'choice4':4, 'choice5':5,
                   'option1':1, 'option2':2, 'option3':3, 'option4':4, 'option5':5}

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

