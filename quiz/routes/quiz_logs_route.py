from quiz import app, db
from flask_login import login_required, current_user
from flask import render_template, flash
from quiz.db_models import *
from quiz.utils import *
from sqlalchemy import desc

# Show the past quiz attempts as a list
@app.route('/quiz-show-logs', methods=['GET','POST'])
@login_required # Don't allow to see quiz logs unless logged-in
def quiz_show_logs():

    quizlog_lst = []
    if current_user.role == 'admin':
        logs = Quizlogs.query.order_by(desc(Quizlogs.date_taken)).all()
    else:
        logs = Quizlogs.query.filter_by(quiz_taker_id=current_user.id).all()

    for log in logs:
        quizlog_detail =  extract_log_details(log, 'list')
        quizlog_lst.append(quizlog_detail)

    return render_template("quiz_show_logs.html",
                           quizlog =quizlog_lst)

# Show the selected quiz attempt details
@app.route('/quiz_show_logs/<int:id>', methods=['GET','POST'])
@login_required # Don't allow to see individual quiz log unless logged-in
def quiz_show_log(id):

    log = Quizlogs.query.get_or_404(id)
    quizlog_detail =  extract_log_details(log, 'detailed')
    quiz_log_id, quiz_taker, quiz_qn_ans_res_img_list, quiz_score, quiz_total, quiz_taken_date = quizlog_detail

    return render_template("quiz_show_log.html",
                           quiz_taker_username=quiz_taker,
                           quiz_qn_ans_res_list=quiz_qn_ans_res_img_list,
                           quiz_score=quiz_score,
                           quiz_total=quiz_total,
                           quiz_taken_date=quiz_taken_date)

# Delete individual quiz logs
@app.route('/quiz_show_logs/delete/<int:id>') # Pass ID of quiz log to be deleted
@login_required #Dont allow to delete a quiz log unless logged-in.
def delete_quiz_log(id):
    logs = Quizlogs.query.order_by(desc(Quizlogs.date_taken)).all()
    quizlog_lst = []
    for log in logs:
        quizlog_detail = extract_log_details(log, 'list')
        quizlog_lst.append(quizlog_detail)

    quizlog_to_delete = Quizlogs.query.get_or_404(id)
    # Only admin can delete the quizlog.
    if current_user.role == 'admin':
        try:
            db.session.delete(quizlog_to_delete)
            db.session.commit()
            flash(f'Quizlog deleted successfully!')
            logs = Quizlogs.query.order_by(desc(Quizlogs.date_taken)).all()
            quizlog_lst = []
            for log in logs:
                quizlog_detail = extract_log_details(log, 'list')
                quizlog_lst.append(quizlog_detail)
            return render_template("quiz_show_logs.html",
                                   quizlog=quizlog_lst)
        except:
            flash('Couldnt delete Question !')
            return render_template("quiz_show_logs.html",
                                   quizlog=quizlog_lst)
    else:
        flash(f'Quizlog Cant be deleted. You are not authorized to delete this quiz attempt')
        return render_template("quiz_show_logs.html",
                               quizlog=quizlog_lst)