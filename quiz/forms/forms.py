from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileAllowed

# Create a login form
class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a Form class that can feed our db for users registered
class UserForm(FlaskForm):
    name = StringField("Name*", validators = [DataRequired()])
    username = StringField("Username*", validators = [DataRequired()])
    email = StringField("Email*(xxx@yzmail.com)", validators=[DataRequired(),Email()])
    role = StringField("User Role ( Please write to a1@gmail.com for admin/creator access )",  validators=[DataRequired()])
    password_hash = PasswordField('Password*', validators=[DataRequired(),
                                                          EqualTo('password_hash2', message='Passwords must match !')])
    password_hash2 = PasswordField('Confirm Password*', validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a Form class for password
class PasswordForm(FlaskForm):
    email = StringField("Enter your email ID", validators = [DataRequired()])
    password_hash = PasswordField("Enter your password", validators=[DataRequired()])
    submit = SubmitField("Submit")

# Create a Form class that can feed our db for questions created
class QuestionForm(FlaskForm):
    question = CKEditorField("Question", validators = [DataRequired()])
    question_type = StringField("Question Type  ",  validators=[DataRequired()])
    question_category = StringField("Question Category  ",  validators=[DataRequired()])
    choice1 = StringField("Answer Choice-1 ")
    choice2 = StringField("Answer Choice-2 ")
    choice3 = StringField("Answer Choice-3 ")
    choice4 = StringField("Answer Choice-4 ")
    choice5 = StringField("Answer Choice-5 ")
    image1 = FileField(label=" Upload Image-1 (if applicable) ",validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    image2 = FileField(label=" Upload Image-2 (if applicable) ",validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    image3 = FileField(label=" Upload Image-3 (if applicable) ",validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    image4 = FileField(label=" Upload Image-4 (if applicable) ",validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    image5 = FileField(label=" Upload Image-5 (if applicable) ",validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    answer = StringField('Answer ', validators=[DataRequired()])
    other_answer1 = CKEditorField("Other Answer1 - Fill in if you chose Other as Answer")
    other_answer2 = CKEditorField("Other Answer2 - Fill in if you chose Other as Answer")
    active_flag = StringField("Question active status : ")
    submit = SubmitField("Submit")

# Create a Form class to host other answer(Fill in the blank) while taking the quiz
class OtherAnswerForm(FlaskForm):
    oth_answer = StringField("Enter the answer", validators = [DataRequired()])

# Create a Form class to host other answer(Fill in the blankS) while taking the quiz
class OtherAnswerForm2(FlaskForm):
    oth_answer1 = StringField("Enter the answer", validators = [DataRequired()])
    oth_answer2 = StringField("Enter the answer", validators = [DataRequired()])

# Create a search form
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")