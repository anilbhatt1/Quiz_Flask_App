## Test-Your-Know-how App

- **Heroku Link** : https://test-your-know-how.herokuapp.com/
- **Features present in app**

![Features](https://github.com/anilbhatt1/Quiz_Flask_App/blob/master/Test_your_know_how_features.png)
    
- **Short Demo - Youtube Link explaining the features (13 mins video)** : https://youtu.be/yGLW6H00ojY

- **Free Youtube References** that helped me develop this app

  - Flask Fridays by Codemy.com https://www.youtube.com/watch?v=0Qxtt4veJIc&list=PLCC34OHNcOtolz2Vd9ZSeSXWc8Bq23yEz&ab_channel=Codemy.com
  - Flask : Upload image to Database https://www.youtube.com/watch?v=lg1k2klqkdQ&list=LL&index=17&ab_channel=CodeJana
  - Modularizing flask application https://www.youtube.com/watch?v=-BC3V1CUKpU&list=LL&index=12&t=56s&ab_channel=JulianNash
  - Modularizing flask application https://www.youtube.com/watch?v=44PvX0Yv368&list=LL&index=11&t=988s&ab_channel=CoreySchafer
  - Flask : Download a file as an attachment https://www.youtube.com/watch?v=sy1MNWt7om4&list=LL&index=9&ab_channel=CodingShiksha
  - Upload files to flask as attachment https://www.youtube.com/watch?v=GeiUTkSAJPs&list=LL&index=8&t=384s&ab_channel=ArpanNeupane
  - Build a timer with flask and javascript https://www.youtube.com/watch?v=9YUy26jb33g&list=LL&index=7&t=766s&ab_channel=teclado

- **File structure**

![File_Struct](https://github.com/anilbhatt1/Quiz_Flask_App/blob/master/Directory_Structure.png)

- Login credentials to take the quiz as a normal user 
    - username : d1 
    - password : d1 

- **Brief explanation of Relevant modules**
    - quiz/db_models
        - __init__.py -> Import statement for db_models.py to work properly in modularized fashion
        - db_models.py
            - SQLITE DB is used for developing this app.
            - This file holds the db definitions for Users, Questions, Quizlogs, Feedbacks tables.
            - This also holds db definitions for temp storage - Quiztemp, Feedbacktemp
    - quiz/feedback_template
        - This folder has 2 files - fb_qn_logic.xlsx and fb_qn_statement.txt
        - fb_qn_logix.xlsx -> This holds the logic to show next feedback question based on the response.
            - For example if response to question 1 is correct then question2 will be displayed else question 7
        - fb_qn_statement.txt -> This holds the feedback questions, responses, correct answer
        - These files will be used in the feedback logic to take feedback on user experience.
    - quiz/forms
        - __init__.py -> Import statement for forms.py to work properly in modularized fashion
        - forms.py -> Flaskforms are used in UI. This file holds forms for different pages of app.
    - quiz/routes
        - __init__.py -> Import statements for various route py files to work properly in modularized fashion
        - error_page_route.py 
            - This holds the common error page logics - 404 and 500
        - plagiarism_route.py
            - Checks the questions uploaded for plagiarism based on cosine similarity
            - Plagiarism score ranges from 0 to 1            
        - questions_route.py
            - Have following functionalities in this module
                - Add a question
                - Deactivate a question so that question remains in DB but wont be considered for quiz
                - Activate a question (that was already deactivated)
                - Delete a question
                - Edit a question
                - Display individual question
                - Display all the questions
                - Download questions to questions.txt file
                - Upload questions using a txt file
                - Check the status of download and upload
        - quiz_logs_route.py
            - Each time a user takes a quiz, a log is created in QuizLogs DB
            - This module shows the logs and deletes the logs (access only for admin)       
        - quiz_run_route.py
            - This module starts the quiz and displays questions one-by-one
            - Also times-out the quiz upon reaching the allowed time
        - user_route.py   
            - Deletes, updates, adds a user
    - quiz/static
        - files
            - This folder has the txt file for uploaded questions and downloaded questions
        - images
            - This folder holds the images required for questions involving images 
    - quiz/templates
        - Holds all the html templates used in UI
    - quiz/utils
        - __init__.py -> Import statements for various route py files to work properly in modularized fashion
        - fn_utils.py 
            - save_image_qn -> Function to save the image as part of adding/editing questions
            - extract_log_details -> Function to extract past quiz attempt details. Used in quiz_logs_route
            - calc_save_quiz_score -> Function to calculate the quiz score upon attempting all the questions and save the details to Quizlogs DB
            - remove_html_tags -> Function to remove html tags from a string
            - temp_quiz_db -> Function to read/update temp_quiz DB. 
                - This temporary DB is used to save the questions, its answers and user responses during quiz
            - prep_feedback_data -> Function to prepare feedback questions and control logic based on the response for each feedback question
            - temp_fb_db -> Function to read/update temp_feedback DB
            - save_to_feedback_db -> Saving the details to Feedback DB before logout
            - create_qn_string -> Create a string separated by '|' for the question supplied in format - id|question|choice1|....
            - create_qn_file_list -> Create a list with questions which will be written to 'questions.txt' file. This file will be downloaded by the user
        - upload_qns_util.py
            - save_qn_file -> Function to save the file that user uploaded as part of upload questions
            - upload_file_process -> Function to process the uploaded file
            - read_upload_file -> Read the uploaded file to a list
            - qn_column_validations -> Validation of questions to check if desired formats are followed
            - check_qn_exists -> Check if question exists based on qn-id supplied
            - check_if_images_exists -> Check if images provided exists in stati/images folder
            - update_record -> If validations are successful, update the question in database (existing question)
            - add_record -> If validations are successful, add the question in database (new question)             
            - create_upload_response_file -> Create the response file for uploaded records
    - quiz/__init__.py
            - Main init file for modularization
    - login.py
        - Holds following functionalities
        - login
        - logout
        - perapring the feedback questions and control flow logic
        - taking feedback and storing it while logout
        - Showing initial home page 
        - show the feedbacks received (access restricted based on user roles)
        - delete the feedbacks received (access only for admin role)
    - quiz_run.py
        - Initial module that launches the app
    - .gitignore
        - Files to be ignored while commiting to git
    - Procfile
        - Required to launch the app in heroku
    - requirements.txt
        - Necessary packages required to run this app
    - users.db
        - SQLITE database having various tables used in the app -  Users, Questions, Quizlogs, Feedbacks etc.
        
    
    