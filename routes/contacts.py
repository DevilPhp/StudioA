from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify

contactsBP = Blueprint('contacts', __name__)

@contactsBP.route('/<lang>/contacts')
def about(lang):
    return render_template(f'/{lang}/index.html')