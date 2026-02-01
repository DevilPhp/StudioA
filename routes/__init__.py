from flask import Blueprint

from .about import aboutBP
from .home import homeBP
from .contacts import contactsBP

blueprints = [
    aboutBP,
    homeBP,
    contactsBP
]