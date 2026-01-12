from flask import Blueprint

from .about import aboutBP
from.home import homeBP

blueprints = [
    aboutBP,
    homeBP
]