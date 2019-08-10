# -*- coding: utf-8 -*-
"""Gpsdb views."""
from datetime import datetime

import gpxpy
import json
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
from motracker.extensions import db
from motracker.user.models import User
from motracker.utils import gpx2geo, flash_errors
from sqlalchemy import text

from .forms import AddFileForm, ApiForm
from .models import ApiKey, Filez, Trackz, Pointz


# SUPPORT FUNCTIONS and CONSTANTS
# -------------------------------

# fake track as default response
faketrack = '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":\
        "LineString","coordinates":[[102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]]}}]}'

# $RMC
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
    trackdate = valuez.datestamp

    return dict(
        timez=timez,
        lat=lat,
        lon=lon,
        speed=speed,
        bearing=bearing,
        trackdate=trackdate
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
            db.session.close()
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
    current_app.logger.debug(query)
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

@blueprint.route("/gpx/<int:gpx_id>")
def gpxtrace(gpx_id):
    """Initiates convertion of GPX into our DB and redirects to show GPX on a map."""
    # TODO: use celery to parse the track
    # check if we have the GPS already rendered, if not, render it
    track = Trackz.query.filter_by(gpx_id=gpx_id).first()
    if not track:
        # get username current user
        track_id = gpx2geo(gpx_id)
    else:
        track_id = track.id
    return redirect(url_for('gpsdb.showtrack',
                            track_id=track_id))


@blueprint.route("/tracks/<string:username>")
def usertracks(username):
    """Lists all tracks for the particular user."""
    # check if username was provided and is valid, else flask sends 404.
    if isinstance(username, str):
        # check if user exists
        userdb = User.query.filter_by(username=username).first_or_404()
        user_id = userdb.id
        # we do not list GPX static files here, only live tracks
        q1 = Trackz.query.filter_by(id=user_id, gpx_id=None).all()
        if q1:
            current_app.logger.debug(q1)
            return render_template(
                "gpsdb/alltracks,html",
                username=username,
            )
        else:
            return render_template('404.html'), 404


@blueprint.route("/show/<int:track_id>")
def showtrack(track_id):
    """Shows track on the map."""
    # check if track_id was provided and is an int, else flask sends 404
    if isinstance(track_id, int):
        # check if track exist
        r1 = Trackz.query.filter_by(id=track_id).first()
        if r1:
            # get username of person who owns the track
            userdb = User.query.filter_by(id=r1.user_id).first_or_404()
            # get name of the track
            trackname = r1.name
            trackdesc = r1.description
            # check if track was rendered from a GPX and that GPX is private
            if r1.gpx_id:
                r2 = Filez.query.filter_by(id=r1.gpx_id).first()
                if r2:
                    if r2.is_private:
                        return render_template('404.html'), 404
        else:
            return render_template('404.html'), 404
        return render_template(
            "gpsdb/showtrack.html",
            track_id=track_id,
            trackname=trackname,
            trackdesc=trackdesc,
            username=userdb.username
        )


@blueprint.route("/realtime/<int:track_id>")
def realtime(track_id):
    """Shows realtime position for a track."""
    # TODO: add possibility for a user to hide (s)hes realtime location.
    # check if username was provided and is valid, else flask sends 404.
    if isinstance(track_id, int):
        # check if track exist
        r1 = Trackz.query.filter_by(id=track_id).first_or_404()
        if r1:
            # check track for username
            userdb = User.query.filter_by(id=r1.user_id).first_or_404()
            return render_template(
                "gpsdb/realtime.html",
                track_id=track_id,
                device=r1.device,
                username=userdb.username
            )


@blueprint.route("/json/<int:track_id>")
def geojson(track_id):
    """Sends a GeoJON built from a track."""
    # fake response is the same for all cases
    fakeresponse = current_app.response_class(
        response=faketrack,
        status=200,
        mimetype='application/json'
    )
    # check if track_id was provided and is an int, else flask sends 404
    if isinstance(track_id, int):
        # check if track exist
        r1 = Trackz.query.filter_by(id=track_id).first()
        if r1:
            # check if track was rendered from a GPX and that GPX is private
            if r1.gpx_id:
                r2 = Filez.query.filter_by(id=r1.gpx_id).first()
                if r2:
                    if r2.is_private:
                        return fakeresponse
        # if track does not exist in our database, we are sending a fake one
        # instead of
        else:
            return fakeresponse
        # here we ask for a specific track in plain SQL as it is simpler

        # we cut results to 6 decimal places as it gives ~11cm accuracy which is enough - but it does not work as subq?
        # sql = text('SELECT ST_AsGeoJSON(ST_MakeLine(ST_Transform(points.geom,4326) ORDER BY points.timez),6) \
        #        FROM points WHERE points.track_id = {};'.format(track_id))

        sql = text('SELECT ST_AsGeoJSON(subq.*) as geojson FROM (SELECT ST_MakeLine(geom ORDER BY timez)\
                   FROM points WHERE track_id = {}) as subq'.format(track_id))
        result = db.session.execute(sql)
        trackjson = result.fetchone()  # TODO: maybe .fetchall() some day?
        current_app.logger.debug(trackjson)
        data = '{"type":"FeatureCollection","features":[' + trackjson[0] + ']}'
        response = current_app.response_class(
            response=data,
            status=200,
            mimetype='application/json'
        )
        db.session.close()
        return response


@blueprint.route("/jsonp/<string:jtype>/<int:track_id>")
def geojsonr(jtype, track_id):
    """Sends a GeoJON built from a track."""
    # fake response is the same for all cases
    fakeresponse = current_app.response_class(
        response=faketrack,
        status=200,
        mimetype='application/json'
    )
    # check if track_id was provided and is an int, else flask sends 404
    if isinstance(track_id, int) and isinstance(jtype, str):
        # check if track exist
        r1 = Trackz.query.filter_by(id=track_id).first()
        if r1:
            # check if track was rendered from a GPX, it is not realtime
            if r1.gpx_id:
                return fakeresponse
            # simplifying things, we are showing last recorded position
            # of specified track
            # q2 = Pointz.query.filter_by(track_id=q1.id).order_by(Pointz.timez.desc()).first()
            # q2 = text('SELECT ST_AsGeoJSON(points.geom ORDER BY points.timez DESC,6) \
            #           FROM points WHERE points.track_id = {}'.format(r1.id))
            if jtype == "one":
                limit = "LIMIT 1"
            else:
                limit = ""
            q2 = text('SELECT ST_AsGeoJSON(subq.*) as geojson FROM (SELECT geom,\
                      id, timez, altitude, speed, bearing, sat, comment from \
                      points WHERE track_id = {} ORDER BY timez DESC {}) \
                      as subq'.format(r1.id, limit))
            current_app.logger.debug(q2)
            result = db.session.execute(q2)
            trackjson = result.fetchall()
            if trackjson:
                # if we have only one point
                if len(trackjson) == 1:
                    y = trackjson[0][0]
                # if we want multiple points
                else:
                    y = ""
                    z = 0
                    for x in trackjson:
                        if z != 0:
                            y += ", "
                        y += (x[0])
                        z += 1
                data = '{"type":"FeatureCollection","features":[' + y + ']}'
                current_app.logger.debug(y)
                response = current_app.response_class(
                    response=data,
                    status=200,
                    mimetype='application/json'
                )
                return response
            else:
                fakeresponse
        else:
            return fakeresponse
        # if track does not exist in our database, we are sending a fake one
        # instead of
    else:
        return fakeresponse


@blueprint.route("/data/opengts")
def opengts():
    """Receives data from OpenGTS compatible receiver device.

    http://www.opengts.org/OpenGTS_Config.pdf
    http://www.geotelematic.com/docs/StatusCodes.pdf
    """
    alt = request.args.get('alt')
    apicode = request.args.get('acct')
    code = request.args.get('code')
    gprmc = request.args.get('gprmc')
    device = request.args.get('id')
    current_app.logger.debug('alt = {}'.format(alt))
    current_app.logger.debug('id = {}'.format(apicode))
    current_app.logger.debug('code = {}'.format(code))
    current_app.logger.debug('device = {}'.format(device))
    current_app.logger.debug('gprmc = {}'.format(gprmc))

    # parsing id to match GNSS Api
    haskey = ApiKey.query.filter_by(apikey=apicode).first()
    if haskey:
        user_id = haskey.user_id
        current_app.logger.info("Found valid API code belonging to User ID = {}.".format(user_id))
    else:
        current_app.logger.info("No user has such an API key = {}. Ignoring request then.".format(id))
        return 'Hello?'

    # code 0xF020 means OpenGTS location reporting
    if code == "0xF020":
        # parsing NMEA-0183 $GPRMC record
        gpsdata = parse_rmc(gprmc)
        current_app.logger.debug('parsed gprmc: {}'.format(gpsdata))
        # checking tracks database for the data and device
        trackdb = Trackz.query.filter_by(trackdate=gpsdata['trackdate'],
                                         device=device).first()
        if trackdb:
            current_app.logger.debug('trackdb: {}'.format(trackdb))
        else:
            # we need to create a track
            trackdb = Trackz.create(
                name="OpenGTS",
                user_id=user_id,
                start=datetime.utcnow(),
                description="LiveTracking",
                device=device,
                trackdate=gpsdata['trackdate']
            )
            current_app.logger.debug('trackdb: {}'.format(trackdb))
        # we have track id, now we must check if the location was not already
        # submitted, as it looks like opengts often tries to resubmit the same
        # points over and over again.
        points = Pointz.query.filter_by(
            track_id=trackdb.id,
            geom='SRID=4326;POINT({} {})'.format(gpsdata['lon'],
                                                 gpsdata['lat']),
            timez=gpsdata['timez']
        ).first()
        if not points:
            # uff, now we can finally submit location
            points = Pointz.create(
                track_id=trackdb.id,
                geom='SRID=4326;POINT({} {})'.format(gpsdata['lon'], gpsdata['lat']),
                altitude=alt,
                timez=gpsdata['timez'],
                speed=gpsdata['speed'],
                bearing=gpsdata['bearing'],
                comment="OpenGTS",
                sat=None,
                vdop=None,
                pdop=None,
                hdop=None,
                provider="gps"
            )
            # at the end we are updating the track table with current time
            current_app.logger.debug(points)
            trackdb.stop = datetime.utcnow()
            db.session.commit
            db.session.close()
        else:
            current_app.logger.debug('We already have that point recorded. Thank you.')
        #
    return 'OK'
