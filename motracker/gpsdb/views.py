# -*- coding: utf-8 -*-
"""Gpsdb views."""

import strgen
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from motracker.extensions import db

from .forms import ApiForm
from .models import ApiKey

blueprint = Blueprint("gpsdb", __name__, url_prefix="/gps", static_folder="../static")


@blueprint.route("/api", methods=["GET", "POST"])
@login_required
def gpsapi():
    """(re)Generate and/or present API key."""
    form = ApiForm(request.form)
    hasapi = ApiKey.query.filter_by(user=current_user).first()
    # Handle regeneration of API key
    if request.method == "POST":
        if form.validate_on_submit():
            apikey = strgen.StringGenerator("[\w\d]{10}").render()
            if hasapi:
                hasapi.apikey = apikey
                db.session.commit()
            else:
                ApiKey.create(
                    user=current_user,
                    apikey=apikey
                )
    # No regeneration request
    if hasapi:
        apikey = hasapi.apikey
    else:
        apikey = strgen.StringGenerator("[\w\d]{10}").render()
        ApiKey.create(
            user=current_user,
            apikey=apikey
        )
    return render_template(
        "gpsdb/apikey.html",
        form=form,
        apikey=apikey)
