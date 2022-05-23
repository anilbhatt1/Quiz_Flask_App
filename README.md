## Test-Your-Know-how App

- **Heroku Link** : https://test-your-know-how.herokuapp.com/
- **Youtube Link explaining the features (13 mins video)** : https://youtu.be/yGLW6H00ojY
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

- **Brief explanation of modules **
    - quiz/db_models
        - __init__.py -> Import statement for db_models.py to work properly in modularized fashion
        - db_models.py
            - SQLITE DB is used for developing this app.
            - This file holds the db definitions for Users, Questions, Quizlogs, Feedbacks databases.
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
        - login_route.py
            - Holds following functionalities
                - login
                - logout
                    - taking feedback and storing it while logout
                - Showing initial home page 
                    - before login, a page with login option will be shown
                    - after login, a page with user details will be shown
                - show the feedbacks received (access restricted based on user roles)
                - delete the feedbacks receibed (access only for admin role)
        - plagiarism_route.py
        - questions_route.py
        - quiz_logs_route.py
        - quiz_run_route.py
        - user_route.py   
