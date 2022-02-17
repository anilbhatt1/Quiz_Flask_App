from quiz import app, db
from PIL import Image
import random, time, os, re
from quiz.routes import *
from quiz.db_models import *
from pandas import read_excel
from collections import namedtuple
from flask_login import login_required, current_user
from fractions import Fraction

num_columns = 20 # Number of columns in questions table
qn_var_names = ['id', 'question', 'question_type','question_category',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5',
                'image1', 'image2', 'image3', 'image4', 'image5',
                'answer', 'other_answer1', 'other_answer2','active_flag','date_added','qn_creator_id']
accepted_qn_types = ['Fill-In-The Blank','Fill-In-The Blanks','numeric','text qn - image answer','image qn - text answer','multiple-choice']
accepted_qn_categories = ['Geography', 'History', 'Maths']
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']

# Function to save the file that user uploaded as part of upload questions.
def save_qn_file(upload_file):

    user_name = current_user.username
    timestr = time.strftime("%Y%m%d")
    file_save_name = str('Uploaded_questions_' + str(user_name) + '_' + str(timestr) + '.txt')
    upload_file_save_path = os.path.join(app.root_path, 'static/files/upload', file_save_name)
    upload_file.save(upload_file_save_path)
    return upload_file_save_path

# Function to process the uploaded file
def upload_file_process(uploaded_file_name):

    upload_response_list = []
    upload_status_list = []
    upload_status = ''

    # Read the file to a list
    upload_lst = read_upload_file(uploaded_file_name)
    # read records one-by-one
    for up_rec in upload_lst:
        if up_rec[:26] == 'id|question|question_type|' or \
           '|' not in up_rec[:5]:  #Ignore header & blank lines
            pass
        else:
            upload_flag = ''
            response = ''
            # Split the uploaded-record based on separator '|' and write to a list
            up_rec_lst = up_rec.split('|')
            if len(up_rec_lst) > 20:
                validate_response = f'Error More columns ({len(up_rec_lst)}) than expected ({num_columns})|'
                validate_status = 0
            elif len(up_rec_lst) < 20:
                validate_response = f'Error Lesser columns ({len(up_rec_lst)}) than expected ({num_columns})||'
                validate_status = 0
            else:
                # If column validation okai, continue with remaining validation
                qn_column_dict = {}
                for idx, var in enumerate(qn_var_names):  # Converting list to a dict like {'id': 1, 'question': 'what is pi ?',...}
                    qn_column_dict[var] = up_rec_lst[idx]

                if qn_column_dict['id'].isnumeric():   # If id is present, action required is update
                    upload_flag = 'update'
                else:                                  # Else, go for add operation
                    upload_flag = 'add'

                validate_response, validate_status = qn_column_validations(qn_column_dict, upload_flag) # Validate the columns

            # If validations successful, update or add the records in database
            if validate_status:
                if upload_flag == 'update':
                    upload_status = update_record(qn_column_dict)
                else:
                    upload_status = add_record(qn_column_dict)

                if upload_status:
                    response = up_rec + '*' + 'Validation Status:|Success' + '*' + f'upload Status for {upload_flag}:|Success'
                else:
                    response = up_rec + '*' + 'Validation Status:|Success' + '*' + f'upload Status for {upload_flag}:|Failed'
            else:
                response = up_rec + '*' + 'Validation Status:|' + str(validate_response) + '*' + f'upload Status for {upload_flag}:|Not uploaded to DB'
                upload_status = validate_status

            upload_response_list.append(response)
            upload_status_list.append(upload_status)
            upload_file_response_path = create_upload_response_file(upload_response_list) # Create the upload response file
    return upload_file_response_path, upload_status_list

# Read the uploaded file to a list
def read_upload_file(uploaded_file_name):

    upload_file_path = os.path.join(app.root_path, 'static/files', uploaded_file_name)
    with open(upload_file_path) as f:
        lst = f.readlines()
    return lst

# Validate the columns
def qn_column_validations(qn_column_dict, upload_type):

    global validate_success
    global error_response
    validate_success = 1
    error_response = ''
    for qn_column in qn_column_dict:
        # Check if question ID exists for update operation
        if qn_column == 'id' and upload_type == 'update':
            qn_id = int(qn_column_dict[qn_column])
            question = check_qn_exists(qn_id)
            if question is None:
                error_response = 'Question ID doesnt exist|'
                validate_success = 0
                break
        # Check if question statement has atleast 5 chars
        elif qn_column == 'question':
            qn_statement = str(qn_column_dict[qn_column])
            if len(qn_statement) < 5:
                error_response = 'Too short question statement|'
                validate_success = 0
                break
        # Check if question-type supplied is valid
        elif qn_column == 'question_type':
            qn_type = str(qn_column_dict[qn_column])
            if qn_type in accepted_qn_types:
                pass
            else:
                error_response = 'Invalid question-type|'
                validate_success = 0
                break
        # Check if question-category supplied is valid one
        elif qn_column == 'question_category':
            qn_category = str(qn_column_dict[qn_column])
            if qn_category in accepted_qn_categories:
                pass
            else:
                error_response = 'Invalid question-category|'
                validate_success = 0
                break

        # If basic validations above are successful,..
    if validate_success:
        # Check if other_answer1 is valid if question_type is fill-in-the-blank
        if qn_column_dict['question_type'] == 'Fill-In-The Blank':
            if qn_column_dict['other_answer1'] == '' or qn_column_dict['other_answer1'] is None:
                error_response = 'other_answer1 blank for Fill-In-The-Blank|'
                validate_success = 0
        # Check if both other_answer1 & other_answer2 are valid if question_type is fill-in-the-blank
        elif qn_column_dict['question_type'] == 'Fill-In-The Blanks':
            if qn_column_dict['other_answer1'] == '' or qn_column_dict['other_answer1'] is None or \
               qn_column_dict['other_answer2'] == '' or qn_column_dict['other_answer2'] is None:
                error_response = 'other_answer1 or other_answer2 blank for Fill-In-The-BlankS|'
                validate_success = 0
        # Check if other_answer1 is int or float if question_type is numeric
        elif qn_column_dict['question_type'] == 'numeric':
            if type(qn_column_dict['other_answer1']) is float or type(qn_column_dict['other_answer1']) is int \
               or str(qn_column_dict['other_answer1']).isnumeric():
                pass
            else:
                try:
                    float(qn_column_dict['other_answer1'])
                except ValueError:
                    error_response = 'other_answer1 non-numeric for Numeric question|'
                    validate_success = 0
        # Check if images supplied as answer for text qn - image answer question_category update are valid and already present in static folder
        elif qn_column_dict['question_type'] == 'text qn - image answer' and upload_type == 'update':
            if qn_column_dict['image1'] == '' or qn_column_dict['image2'] == '' or qn_column_dict['image3'] == '' or \
               qn_column_dict['image4'] == '' or qn_column_dict['image5'] == '' :
                error_response = 'Image answer missing for text qn - image answer question|'
                validate_success = 0
            else:
                image_val_status, image_val_response = check_if_images_exists([qn_column_dict['image1'],
                                                                               qn_column_dict['image2'],
                                                                               qn_column_dict['image3'],
                                                                               qn_column_dict['image4'],
                                                                               qn_column_dict['image5']])
                if image_val_status:
                    pass
                else:
                    error_response = image_val_response
                    validate_success = 0
        # Reject addition of text qn - image answer question_category
        elif qn_column_dict['question_type'] == 'text qn - image answer' and upload_type == 'add':
            error_response = 'upload not allowed for adding text qn - image answer questions. Please use Add-question UI tab|'
            validate_success = 0
        # Check if image1 & choices supplied as answers for image qn - text answer question_category update are valid and image already present in static folder
        elif qn_column_dict['question_type'] == 'image qn - text answer' and upload_type == 'update':
            if qn_column_dict['image1'] == '':
                error_response = 'Image missing for image qn - text answer question|'
                validate_success = 0
            elif qn_column_dict['choice1'] == '' or qn_column_dict['choice1'] is None or \
                 qn_column_dict['choice2'] == '' or qn_column_dict['choice2'] is None or \
                 qn_column_dict['choice3'] == '' or qn_column_dict['choice3'] is None or \
                 qn_column_dict['choice4'] == '' or qn_column_dict['choice4'] is None or \
                 qn_column_dict['choice5'] == '' or qn_column_dict['choice5'] is None:
                error_response = 'Answer choice missing for image qn - text answer question|'
                validate_success = 0
            else:
                image_val_status, image_val_response = check_if_images_exists([qn_column_dict['image1']])
                if image_val_status:
                    pass
                else:
                    error_response = image_val_response[:49] + 'image qn - text answer question|'
                    validate_success = 0
        # Reject addition of image qn - text answer question_category
        elif qn_column_dict['question_type'] == 'image qn - text answer' and upload_type == 'add':
            error_response = 'upload not allowed for adding image qn - text answer questions. Please use Add-question UI tab|'
            validate_success = 0

        # Check if choices supplied are valid for multiple-choice type questions
        elif qn_column_dict['question_type'] == 'multiple-choice':
            if qn_column_dict['choice1'] == '' or qn_column_dict['choice1'] is None or \
               qn_column_dict['choice2'] == '' or qn_column_dict['choice2'] is None or \
               qn_column_dict['choice3'] == '' or qn_column_dict['choice3'] is None or \
               qn_column_dict['choice4'] == '' or qn_column_dict['choice4'] is None or \
               qn_column_dict['choice5'] == '' or qn_column_dict['choice5'] is None:
                error_response = 'Answer choice missing for multiple-choice question|'
                validate_success = 0

    return error_response, validate_success

# Check if question exists based on qn-id supplied
def check_qn_exists(qn_id):

    question = Questions.query.filter_by(id=qn_id).first()
    return question

# Check if images provided exists in stati/images folder
def check_if_images_exists(img_path_lst):
    image_val_status = 1
    image_val_response = ''
    for idx, img_name in enumerate(img_path_lst,1):
        img_path = os.path.join(app.root_path, 'static/images', img_name)
        if os.path.isfile(img_path):
            pass
        else:
            image_val_status = 0
            image_val_response = f"{img_name} given for image{idx} doesnt exist for text qn - image answer question|"
            break
    return image_val_status, image_val_response

# If validations are successful, update the record in database
def update_record(qn_column_dict):

    update_status = 0
    qn_id = int(qn_column_dict['id'])
    question = Questions.query.filter_by(id=qn_id).first()
    if qn_column_dict['active_flag'] != 'Inactive':
        question.question=qn_column_dict['question']
        question.question_type=qn_column_dict['question_type']
        question.question_category=qn_column_dict['question_category']
        question.choice1=qn_column_dict['choice1']
        question.choice2=qn_column_dict['choice2']
        question.choice3=qn_column_dict['choice3']
        question.choice4=qn_column_dict['choice4']
        question.choice5=qn_column_dict['choice5']
        question.image1=qn_column_dict['image1']
        question.image2=qn_column_dict['image2']
        question.image3=qn_column_dict['image3']
        question.image4=qn_column_dict['image4']
        question.image5=qn_column_dict['image5']
        question.other_answer1=qn_column_dict['other_answer1']
        question.other_answer2=qn_column_dict['other_answer2']
        question.active_flag='Active'
        question.answer=qn_column_dict['answer']
    else:
        question.active_flag = 'Inactive'

    try:
        db.session.commit()
        update_status = 1
        return update_status
    except:
        return update_status

# If validations are successful, add the record in database
def add_record(qn_column_dict):
    add_status = 0
    question = Questions(question=qn_column_dict['question'],
                         question_type=qn_column_dict['question_type'],
                         question_category=qn_column_dict['question_category'],
                         choice1=qn_column_dict['choice1'],
                         choice2=qn_column_dict['choice2'],
                         choice3=qn_column_dict['choice3'],
                         choice4=qn_column_dict['choice4'],
                         choice5=qn_column_dict['choice5'],
                         image1='default.jpg',
                         image2='default.jpg',
                         image3='default.jpg',
                         image4='default.jpg',
                         image5='default.jpg',
                         other_answer1=qn_column_dict['other_answer1'],
                         other_answer2=qn_column_dict['other_answer2'],
                         active_flag='Active',
                         qn_creator_id=current_user.id,
                         # We are passing current_user.id as qn_creator_id (foreign key). This will get saved in DB
                         answer=qn_column_dict['answer'])
    try:
        db.session.add(question)
        db.session.commit()
        add_status = 1
        return add_status
    except:
        return add_status

# Create the response file for upload records
def create_upload_response_file(upload_response_list):
    user_name = current_user.username
    response_file_name = str('Uploaded_questions_response_' + str(user_name) + '.txt')
    file_save_path = os.path.join(app.root_path, 'static/files/upload_response', response_file_name)
    response_file = open(file_save_path, 'w')
    for item in upload_response_list:
        response_file.write(item + '\n')
    response_file.close()
    return file_save_path



