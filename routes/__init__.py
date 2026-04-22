from flask import Blueprint

from .about import aboutBP
from .home import homeBP
from .contacts import contactsBP
from .auth import authBP
from .admin import adminBP

blueprints = [
    aboutBP,
    homeBP,
    contactsBP,
    authBP,
    adminBP,
]