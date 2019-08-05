# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required
from .models import User

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route("/<string:username>")
def userpage(username):
    """Shows a home page for a user."""
    q1 = User.query.filter_by(username=username).first()
    if q1:
        return render_template(
            "users/showoff.html",
            firstname=q1.first_name,
            lastname=q1.last_name
        )
    else:
        return render_template('404.html'), 404
