from flask_login import login_required, current_user
from flask import render_template, flash
from sqlalchemy import desc
from quiz import app, db
from quiz.db_models import *

# Show the feedbacks recorded as a list
@app.route('/show_feedbacks', methods=['GET','POST'])
@login_required # Don't allow to see feedbacks unless logged-in
def show_feedbacks():

    feedbacks_lst = []
    if current_user.role == 'admin':
        feedbacks =Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()

        for fb in feedbacks:
            fb_detail =  (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
            feedbacks_lst.append(fb_detail)

        return render_template("show_feedbacks.html",
                               feedbacks_lst =feedbacks_lst)

# Delete individual feedbacks
@app.route('/show_feedbacks/delete/<int:id>') # Pass ID of feedback to be deleted
@login_required #Dont allow to delete feedback unless logged-in.
def delete_feedback(id):
    feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()
    feedbacks_lst = []
    for fb in feedbacks:
        fb_detail =  (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
        feedbacks_lst.append(fb_detail)

    feedback_to_delete = Feedbacks.query.get_or_404(id)
    # Only admin can delete the feedback.
    if current_user.role == 'admin':
        try:
            db.session.delete(feedback_to_delete)
            db.session.commit()
            flash(f'Feedback deleted successfully!')
            feedbacks = Feedbacks.query.order_by(desc(Feedbacks.date_of_feedback)).all()
            feedbacks_lst = []
            for fb in feedbacks:
                fb_detail = (fb.id, fb.feedback_giver_name, fb.date_of_feedback, fb.feedback_details)
                feedbacks_lst.append(fb_detail)
            return render_template("show_feedbacks.html",
                                   feedbacks_lst =feedbacks_lst)
        except:
            flash('Couldnt delete feedback !')
            return render_template("show_feedbacks.html",
                                   feedbacks_lst =feedbacks_lst)
    else:
        flash(f'Feedback Cant be deleted. You are not authorized to delete this feedback')
        return render_template("show_feedbacks.html",
                               feedbacks_lst =feedbacks_lst)
