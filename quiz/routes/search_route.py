from quiz import app
from flask_login import login_required
from quiz.forms import *
from quiz.db_models import *
from flask import render_template
from sqlalchemy import desc

# Pass stuff to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)
    # This will pass variable to base.html. Since base.html includes navbar.html, navbar.html will automatically receive it

# Create search functionality
@app.route('/search',methods=['POST'])
@login_required # Don't allow to search unless logged-in
def search():
    form = SearchForm()
    if form.validate_on_submit():
        # Get data i.e. string to be searched from submitted form (html)
        searched = form.searched.data
        # Query the Questions database for search string. Query searches for approx. match
        qns = Questions.query.filter(Questions.question.like('%' + searched + '%'))
        # Order the results based on date created
        qns = qns.order_by(desc(Questions.date_added)).all()

        return render_template('search.html',
                               form=form,
                               searched=searched,
                               qns=qns)