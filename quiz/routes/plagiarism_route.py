from quiz import app, db
from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from quiz.forms import *
from quiz.db_models import *
from quiz.utils import *
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Check questions for plagiarism
@app.route('/questions/plagiarism_check/<int:id>')
@login_required #Dont allow to check unless logged-in.
def question_plagiarism_check(id):
    questions = Questions.query.order_by(Questions.id)
    question_to_check = Questions.query.filter_by(id=id).first()

    qn_master_lst = []
    qn_master_id_lst = []
    qn_lst = []
    sep = '|'
    qn_var_names = ['id', 'question', 'choice1','choice2','choice3','choice4','choice5','answer','other_answer1','other_answer2']
    plagiarism_results = []
    global s_vectors

    for qn in questions:
        var_dict = vars(qn)
        qn_string = create_qn_string(var_dict, qn_var_names, sep)
        qn_master_lst.append(qn_string)
        qn_master_id_lst.append(str(qn.id))
        qn_lst.append(qn.question)

    vectorize = lambda Text: TfidfVectorizer().fit_transform(Text).toarray()
    similarity = lambda doc1, doc2: cosine_similarity([doc1, doc2])
    vectors = vectorize(qn_master_lst)
    s_vectors = list(zip(qn_master_id_lst, vectors, qn_lst))
    idx = qn_master_id_lst.index(str(id))  # Find the index at which question whose plagiarism need to checked is placed in qn_master_id_lst
    check_vector = s_vectors[idx]     # Extract the vector of question whose plagiarism need to be checked from s_vectors based on index we got
    qn_to_check_id, text_vector_qn_to_check, qn_to_check = check_vector  # Do tuple unpacking to store id and vector of qn whose plagiarism is to be checked

    for qn_id, text_vector_qn, qn_db in s_vectors:
        sim_score = similarity(text_vector_qn_to_check, text_vector_qn)[0][1]
        score = (qn_to_check_id, qn_id, sim_score, qn_db)
        plagiarism_results.append(score)
    return render_template("plagiarism_results.html",
                           plag_scores=plagiarism_results,
                           qn_id = qn_to_check_id,
                           qn = question_to_check)



