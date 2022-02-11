from quiz import app
from quiz.utils import *

user_response= ''

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
           next_qn_id = temp_quiz_db('update-response', user_response)
        else:
           next_qn_id = temp_quiz_db('read-next-qn-id', '')

        if next_qn_id == 9999:  # Upon end-of questions, next_qn_id will be updated with 9999
            quiz_question_id_lst, quiz_answer_lst, quiz_response_lst = temp_quiz_db('read', '')
            quiz_score, quiz_total = calc_save_quiz_score(quiz_question_id_lst, quiz_answer_lst, quiz_response_lst,
                                                          current_user.id)
            _ = temp_quiz_db('delete', '')
            flash(f'Quiz completed successfully ! ')
            return render_template("quiz_score.html",
                                    quiz_score=quiz_score,
                                    quiz_total=quiz_total,)
        else:
            oth_form = OtherAnswerForm()
            question = Questions.query.filter_by(id=next_qn_id).first()
            image_choice_list = [('A', question.image1),
                                 ('B', question.image2),
                                 ('C', question.image3),
                                 ('D', question.image4),
                                 ('E', question.image5)]
            oth_form.oth_answer.data = ''
            return render_template("quiz_questions.html",
                                    image_choices=image_choice_list,
                                    question=question,
                                    oth_form=oth_form,)

    elif request.method == 'GET':   # Initial flow reaches here
        _ = temp_quiz_db('delete', '')   # Cleaning-up temp DB record incase if any past records for same user is present
        temp_quiz_db('create', '')       # Creating a temp record with qn IDs to be used in quiz, their answers & 1st qn id
        return render_template("start_quiz.html")







