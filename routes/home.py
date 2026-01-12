from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify

homeBP = Blueprint('home', __name__)

@homeBP.route('/BG/')
@homeBP.route('/BG/index.html')
def homeBG():
    return render_template('BG/index.html')