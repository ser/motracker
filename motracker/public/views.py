# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from motracker.extensions import login_manager, ws
from motracker.public.forms import LoginForm
from motracker.user.forms import RegisterForm
from motracker.user.models import User
from motracker.utils import flash_errors, track_live

import redis
import time

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.debug("Hello from the home page!")
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    if current_user.get_id():
        current_user_live_track = track_live(current_user.get_id())
    else:
        current_user_live_track = None
    return render_template("public/home.html", form=form,
                           current_user_live_track=current_user_live_track)


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)

@ws.route('/rt/<string:track_id>')
def echo(ws, track_id):
    """Websockets serving tracks."""
    reddy = redis.Redis(host='localhost', port=6379, db=3)
    subs = reddy.pubsub()
    subs.subscribe("{}".format(track_id))
    while True:
        t_end = time.time() + 29
        while time.time() < t_end:
            msg = subs.get_message()
            if msg:
                print("received from redis: {}".format(msg))
                ws.send("UP")
            else:
                time.sleep(0.01)
        ws.send("WS PING")
