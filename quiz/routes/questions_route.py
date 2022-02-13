from quiz import app, db
from flask import Flask, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_ckeditor import  CKEditor, CKEditorField
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *

accepted_qn_types = ['Fill-In-The Blank','Fill-In-The Blanks','numeric','text qn - image answer','image qn - text answer','multiple-choice']
accepted_qn_categories = ['Geography', 'History']
answer_types = ['image1', 'image2', 'image3', 'image4', 'image5', 'other',
                'choice1', 'choice2', 'choice3', 'choice4', 'choice5']

# Add Question page
@app.route('/add-qn', methods=['GET','POST'])
#@login_required --> Dont allow to add questions unless logged-in. But we can handle this add_qn.html page as well.
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        qn_creator = current_user.id
        form_images_list = [form.image1.data, form.image2.data, form.image3.data, form.image4.data, form.image5.data]
        current_name_list = []
        image_filename_list = save_image_qn(form_images_list, current_name_list, 'add')
        question = Questions(question=form.question.data,      # We are saving to the database using Questions() model we created above
                             question_type=form.question_type.data,
                             question_category=form.question_category.data,
                             choice1=form.choice1.data,
                             choice2=form.choice2.data,
                             choice3=form.choice3.data,
                             choice4=form.choice4.data,
                             choice5=form.choice5.data,
                             image1=image_filename_list[0],
                             image2=image_filename_list[1],
                             image3=image_filename_list[2],
                             image4=image_filename_list[3],
                             image5=image_filename_list[4],
                             other_answer1=form.other_answer1.data,
                             other_answer2=form.other_answer2.data,
                             active_flag='Active',
                             qn_creator_id = qn_creator,  # We are passing current_user.id as qn_creator_id (foreign key). This will get saved in DB
                             answer=form.answer.data)
        # After clicking the submit button in form we need to clear the entered values
        form.question.data = ''
        form.question_type.data = ''
        form.question_category.data = ''
        form.choice1.data = ''
        form.choice2.data = ''
        form.choice3.data = ''
        form.choice4.data = ''
        form.choice5.data = ''
        form.image1.data = ''
        form.image2.data = ''
        form.image3.data = ''
        form.image4.data = ''
        form.image5.data = ''
        form.answer.data = ''
        form.other_answer1.data = ''
        form.other_answer2.data = ''
        form.active_flag = ''

        # Add the values entered web via form to database
        db.session.add(question)
        db.session.commit()

        # Return a success message if reached this far
        flash("Question Added successfully")

    # Redirect to the webpage
    return render_template('add_qn.html',
                           form=form,
                           qn_types=accepted_qn_types,
                           qn_categories=accepted_qn_categories,
                           answer_types=answer_types
                           )

# Deactivate individual questions
@app.route('/questions/deactivate/<int:id>') # Pass ID of question to be deactiavted
@login_required #Dont allow to deactivate a question unless logged-in.
def deactivate_question(id):
    question_to_deactivate = Questions.query.get_or_404(id)
    id = current_user.id
    # Only creator/admin can deactivate the question. So get creator id via backref
    if id == question_to_deactivate.qn_creator.id or current_user.role == 'admin':
        try:
            question_to_deactivate.active_flag = 'Inactive'
            db.session.add(question_to_deactivate)
            db.session.commit()
            flash(f'Question "{question_to_deactivate.question[:20]}.." deactivated successfully!')
            # Redirect to posts page after successful deactivation
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
        except:
            flash('Couldnt deactivate Question !')
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
    else:
        flash(f'Question Cant be deactivated. You are not authorized to deactivate "{question_to_deactivate.question[:20]}" you selected !')
        questions = Questions.query.order_by(Questions.date_added)
        return render_template("questions.html", questions=questions)

# Activate individual questions
@app.route('/questions/activate/<int:id>') # Pass ID of question to be actiavted
@login_required #Dont allow to activate a question unless logged-in.
def activate_question(id):
    question_to_activate = Questions.query.get_or_404(id)
    id = current_user.id
    # Only creator/admin can activate the question. So get creator id via backref
    if id == question_to_activate.qn_creator.id or current_user.role == 'admin':
        try:
            question_to_activate.active_flag = 'Active'
            db.session.add(question_to_activate)
            db.session.commit()
            flash(f'Question "{question_to_activate.question[:20]}.." Activated successfully!')
            # Redirect to posts page after successful activation
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
        except:
            flash('Couldnt activate Question !')
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
    else:
        flash(f'Question Cant be activated. You are not authorized to activate "{question_to_activate.question[:20]}" you selected !')
        questions = Questions.query.order_by(Questions.date_added)
        return render_template("questions.html", questions=questions)

# Delete individual questions
@app.route('/questions/delete/<int:id>') # Pass ID of question to be deleted
@login_required #Dont allow to delete a question unless logged-in.
def delete_question(id):
    question_to_delete = Questions.query.get_or_404(id)
    id = current_user.id
    # Only creator/admin can delete the question. So get creator id via backref
    if id == question_to_delete.qn_creator.id or current_user.role == 'admin':
        try:
            current_img_name_list = [question_to_delete.image1,
                                     question_to_delete.image2,
                                     question_to_delete.image3,
                                     question_to_delete.image4,
                                     question_to_delete.image5]
            db.session.delete(question_to_delete)
            db.session.commit()
            # Remove images if any from static folder
            for images in current_img_name_list:
                if images is None:  # This means there are no images & hence no action needed
                    pass
                else:
                    img_remove_name = images  # Get the image file name for removal
                    image_remove_path = os.path.join(app.root_path, 'static/images', img_remove_name)
                    os.remove(image_remove_path)

            flash(f'Question "{question_to_delete.question[:20]}.." deleted successfully!')
            # Redirect to questions page after successful deletion
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
        except:
            flash('Couldnt delete Question !')
            questions = Questions.query.order_by(Questions.date_added)
            return render_template("questions.html", questions=questions)
    else:
        flash(f'Question Cant be deleted. You are not authorized to delete "{question_to_delete.question[:20]}" you selected !')
        questions = Questions.query.order_by(Questions.date_added)
        return render_template("questions.html", questions=questions)

# Edit individual questions from respective pages
@app.route('/questions/edit/<int:id>', methods=['GET','POST'])
@login_required # Don't allow to edit question unless logged-in
def edit_question(id):
    question = Questions.query.get_or_404(id)
    form = QuestionForm()
    if form.validate_on_submit():
        question.question = form.question.data
        question.question_type = form.question_type.data
        question.question_category = form.question_category.data
        question.choice1 = form.choice1.data
        question.choice2 = form.choice2.data
        question.choice3 = form.choice3.data
        question.choice4 = form.choice4.data
        question.choice5 = form.choice5.data
        question.answer = form.answer.data
        form_images_list = [form.image1.data, form.image2.data, form.image3.data, form.image4.data, form.image5.data]
        current_img_name_list = [question.image1, question.image2, question.image3, question.image4, question.image5]
        image_filename_list = save_image_qn(form_images_list, current_img_name_list, 'edit')
        question.image1 = image_filename_list[0]
        question.image2 = image_filename_list[1]
        question.image3 = image_filename_list[2]
        question.image4 = image_filename_list[3]
        question.image5 = image_filename_list[4]
        question.other_answer1 = form.other_answer1.data
        question.other_answer2 = form.other_answer2.data
        question.active_flag = 'Active'
        # Update database
        db.session.commit()
        # Remove old images from static folder
        for idx, images in enumerate(form_images_list):
            if images is None: # This means user didnt upload any new images & hence old image continue to hold
                pass
            else:
                img_remove_name = current_img_name_list[idx] #Get the replaced image file name for removal
                image_remove_path = os.path.join(app.root_path, 'static/images', img_remove_name)
                os.remove(image_remove_path)
        flash('Question edited successfully !')
        return redirect(url_for('question', id=question.id))  # This will redirect to the individual question page

    # When we press the 'edit question' button in UI, this is where the control will first come
    # Hence putting 'if' condition here to prevent un-authorized users from editing the post
    if current_user.id == question.qn_creator_id or current_user.role == 'admin':
        form.question.data = question.question
        form.question_type.data = question.question_type
        form.question_category.data = question.question_category
        form.choice1.data = question.choice1
        form.choice2.data = question.choice2
        form.choice3.data = question.choice3
        form.choice4.data = question.choice4
        form.choice5.data = question.choice5
        form.answer.data = question.answer
        form.other_answer1.data = question.other_answer1
        form.other_answer2.data = question.other_answer2
        form.active_flag = question.active_flag
        return render_template('edit_question.html',
                                form=form,
                                image1 = question.image1,
                                image2 = question.image2,
                                image3 = question.image3,
                                image4 = question.image4,
                                image5 = question.image5,
                                qn_types=accepted_qn_types,
                                qn_categories=accepted_qn_categories,
                                answer_types=answer_types,
                                )
    else:
        flash(f'You are not authorized to edit "{question.question[:20]}" you selected !')
        questions = Questions.query.order_by(Questions.date_added)
        return render_template("questions.html", questions=questions)

# Display individual questions created
@app.route('/questions/<int:id>')
def question(id):
    question = Questions.query.get_or_404(id)
    image_choice_list   = [(1, question.image1),
                           (2, question.image2),
                           (3, question.image3),
                           (4, question.image4),
                           (5, question.image5)]
    return render_template("question.html",
                           question=question,
                           image_choices=image_choice_list)

# Display summary of all questions written
@app.route('/questions')
def questions():
    # Grab questions from database in the date order they were written
    questions = Questions.query.order_by(Questions.date_added)
    return render_template("questions.html",
                           questions=questions)
