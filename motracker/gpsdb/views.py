# -*- coding: utf-8 -*-
"""Gpsdb views."""

from datetime import datetime

import gpxpy
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

# from motracker.extensions import celery, db, filez
from motracker.extensions import db, filez
from motracker.utils import flash_errors

from .forms import AddFileForm, ApiForm
from .models import ApiKey, Filez, Pointz, Trackz

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
    timez = datetime.combine(valuez.datestamp, valuez.timestamp)

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
    hasapi = ApiKey.query.filter_by(user_id=current_user.get_id()).first()
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
            user_id=current_user.get_id(),
            apikey=apikey
        )
    return render_template(
        "gpsdb/apikey.html",
        form=form,
        apikey=apikey)


@blueprint.route("/files", methods=["GET", "POST"])
@login_required
def filezsave():
    """Upload previously recorded tracks."""
    form = AddFileForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Verify if the GPX is valid
            file = request.files['upload_file']
            try:
                # At the moment we support UTF-8 files and compatible only
                parsedfile = file.stream.read().decode('utf-8')
                ourgpx = gpxpy.parse(parsedfile)
                # file is parsing, so we are extracting basic interesting data about it
                length_2d = ourgpx.length_2d()
                length_3d = ourgpx.length_3d()
                moving_time, stopped_time, moving_distance, stopped_distance, max_speed = ourgpx.get_moving_data()
                uphill, downhill = ourgpx.get_uphill_downhill()
                start_time, end_time = ourgpx.get_time_bounds()
                points_no = len(list(ourgpx.walk(only_points=True)))
            except Exception as e:
                current_app.logger.info(e)
                flash("Uploaded file is not a valid GPX. Try another one.", "warning")
                query = Filez.query.filter_by(user_id=current_user.get_id()).all()
                return render_template(
                    "gpsdb/filez.html",
                    allfilez=query,
                    form=form)
            dbfile = Filez.create(
                user_id=current_user.get_id(),
                is_private=form.is_private.data,
                description=form.description.data
            )
            # all tracks are saved with filename which is equal to database ID
            fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(dbfile.id) + ".gpx"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(parsedfile)
            fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(dbfile.id) + ".txt"
            with open(fname, "w", encoding="utf-8") as f:
                try:
                    f.write("Number of points: {}\n".format(points_no))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Start time: {}\n".format(start_time))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("End time: {}\n".format(end_time))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("2D length: {}\n".format(length_2d))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("3D length: {}\n".format(length_3d))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Moving time: {}\n".format(moving_time))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Stopped time: {}\n".format(stopped_time))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Moving distance: {}\n".format(moving_distance))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Stopped distance: {}\n".format(stopped_distance))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Max speed: {}\n".format(max_speed))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Uphill: {}\n".format(uphill))
                except Exception as e:
                    current_app.logger.debug(e)
                try:
                    f.write("Downhill: {}\n".format(downhill))
                except Exception as e:
                    current_app.logger.debug(e)
            flash("Successfully uploaded your GPX file.", "info")
            current_app.logger.debug("Saved File: " + str(dbfile.id) + ".gpx")
        else:
            flash_errors(form)
    # Present all files belonging to user
    query = Filez.query.filter_by(user_id=current_user.get_id()).all()
    gpxq = {}
    for x in query:
        # A brief description presentation
        fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(x.id) + ".txt"
        with open(fname, 'r', encoding="utf-8") as f:
            read_file = f.readlines()
            gpxq[x.id] = read_file
    return render_template(
        "gpsdb/filez.html",
        allfilez=query,
        gpxq=gpxq,
        form=form)

@blueprint.route("/gpxtrace/<int:gpx_id>")
def gpxtrace(gpx_id):
    """Initiates convertion of GPX into our DB and redirects to show GPX on a map."""
    from motracker.utils import gpx2geo
    gpx2geo(gpx_id)
    return render_template(
        "gpsdb/showtrack.html",
    )

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
