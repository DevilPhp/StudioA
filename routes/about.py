from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify

aboutBP = Blueprint('about', __name__)

@aboutBP.route('/<lang>/about')
def about(lang):
    return render_template(f'/{lang}/about.html')