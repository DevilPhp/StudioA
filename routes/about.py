from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify

aboutBP = Blueprint('about', __name__)

@aboutBP.route('/')
def about():
    return render_template('/BG/about.html')