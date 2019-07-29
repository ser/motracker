# -*- coding: utf-8 -*-
"""Gpsdb views."""

import datetime
import pynmea2
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
from motracker.utils import flash_errors

from .forms import ApiForm
from .models import ApiKey, Pointz, Trackz

# SUPPORT FUNCTIONS

def parse_rmc(gprmc):
    """Parsing NMEA-0183 $RMC record into more human set of values.

    Recommended Minimum Specific GPS/TRANSIT Data:
    parser library: https://github.com/Knio/pynmea2
    """
    valuez = pynmea2.parse(gprmc)
    lat = valuez.latitude
    lon = valuez.longitude
    speed = valuez.spd_over_grnd
    bearing = valuez.true_course
    timez = datetime.datetime.combine(valuez.datestamp, valuez.timestamp)

    return(
        timez,
        lat,
        lon,
        speed,
        bearing
    )


###########
# MAIN PART
blueprint = Blueprint("gpsdb", __name__, url_prefix="/gnss", static_folder="../static")


@blueprint.route("/apikey", methods=["GET", "POST"])
@login_required
def gpsapi():
    """(re)Generate and/or present API key."""
    form = ApiForm(request.form)
    hasapi = ApiKey.query.filter_by(user=current_user).first()
    # Handle regeneration of API key
    if request.method == "POST":
        if form.validate_on_submit():
            apikey = strgen.StringGenerator("[\w\d]{10}").render()
            hasapi.apikey = apikey
            db.session.commit()
            current_app.logger.info("API key has been changed.")
            flash("API key has been changed.", "info")
        else:
            flash_errors(form)
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

@blueprint.route("/data/opengts")
def opengts():
    """Receives data from OpenGTS compatible receiver device.

    http://www.opengts.org/OpenGTS_Config.pdf
    http://www.geotelematic.com/docs/StatusCodes.pdf
    """
    id = request.args.get('id')
    code = request.args.get('code')
    gprmc = request.args.get('gmprc')

    # parsing id to match GNSS Api
    haskey = ApiKey.query.filter_by(apikey=id).first()
    if haskey:
        user_id = haskey.user_id
        current_app.logger.info("Found valid API ket belonging to %s." %
                                haskey.user)
    else:
        current_app.logger.info("No user has such an API key. Ignoring request.")
        return f'Hello?'

    # parsing NMEA-0183 $GPRMC record
    if code == "0xF020":
        pass
