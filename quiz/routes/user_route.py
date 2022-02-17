from quiz import app
from quiz import db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from quiz.forms import *
from quiz.db_models import *
import re

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
accepted_user_roles = ['creator','admin','normal-user']

# Delete an existing User from list
@app.route('/delete/<int:id>')
@login_required #Dont allow to delete user unless logged-in.
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User deleted successfully')
        our_users = Users.query.order_by(Users.date_added)
        return render_template('dashboard.html',
                               our_users=our_users)

    except:
        flash('Error in Deleting the record!')
        our_users = Users.query.order_by(Users.date_added)
        return render_template('dashboard.html',
                               our_users=our_users)

# Update Database record for existing user
@app.route('/update/<int:id>', methods=['GET','POST'])
@login_required #Dont allow to edit user unless logged-in.
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        valid_email = isValid(name_to_update.email)
        name_to_update.role = request.form['role']
        if name_to_update.role.lower() in accepted_user_roles and valid_email:
            try:
                db.session.commit()
                flash('User Updated successfully')
                return render_template('dashboard.html',
                                       our_users='')
            except:
                flash('Error in Updating the records!')
                return render_template('update.html',
                                       form=form,
                                       name_to_update = name_to_update,
                                       id =id)
        else:
            if not valid_email:
                flash(f'User cant be updated ! Email given {name_to_update.email} is not valid. Please give valid email.')
            else:
                flash(f'User cant be updated ! User role selected invalid. Select user role from {accepted_user_roles}')
            return render_template('update.html',
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
    else:
        return render_template('update.html',
                               form=form,
                               name_to_update=name_to_update,
                               id =id)

# Add a new user
@app.route('/user/add-user', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()  #This shouldn't return any result as email need to be unique
        if user is None:   #if user is None, then execute logic to add new user
            hashed_pwd = generate_password_hash(form.password_hash.data, 'sha256') # We are passing password entered in form to be converted to hash
            if form.email.data == 'a1@gmail.com' or form.email.data == 'r1@gmail.com' or form.email.data == 'tsai@gmail.com':
                role_user = form.role.data.lower()
            else:
                role_user = 'normal-user'
            user = Users(name=form.name.data,
                         username=form.username.data,
                         email=form.email.data,
                         role=role_user,
                         password_hash=hashed_pwd)  # Here is where we are saving to database, so pass hashed_pwd here so that hashed password gets saved in database
            db.session.add(user)
            db.session.commit()
            name = form.name.data
            form.name.data = ''
            form.username.data = ''
            form.email.data = ''
            form.role.data = ''
            form.password_hash.data = ''
            flash(f" Registered Successfully as a {role_user}")
            return render_template("add_user.html",
                                   form=form,
                                   name=name,
                                   user_roles=accepted_user_roles)
        else:
            flash(f"Unable to register. User with {form.email.data} already exists")


    flash(f"Please ensure that all the required fields are filled correctly")
    return render_template("add_user.html",
                           form = form,
                           name = name,
                           user_roles = accepted_user_roles)

def isValid(email):
    if re.fullmatch(regex, email):
      return 1
    else:
      return 0




