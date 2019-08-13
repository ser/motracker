# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, current_app, render_template
from flask_login import login_required
from .models import User

from motracker.gpsdb.models import Trackz

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route("/<string:username>")
def userpage(username):
    """Shows a home page for a user."""
    q1 = User.query.filter_by(username=username).first_or_404()
    # find all tracks belonging to user
    q2 = Trackz.query.filter_by(user_id=q1.id).all()
    # check if user has not set privacy flag
    if not q1.is_private and q2:
        current_app.logger.debug('Found {} tracks for user {}.'.format(len(q2),
                                                                       username))
        return render_template(
            "users/showoff.html",
            firstname=q1.first_name,
            lastname=q1.last_name,
            username=username,
            trackz=q2
        )
    else:  # page is private
        return render_template('404.html'), 404
