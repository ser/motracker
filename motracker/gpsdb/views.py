# -*- coding: utf-8 -*-
"""Gpsdb views."""

import binascii
import gpxpy
import json
import pynmea2
import re
import redis
import strgen
import uuid
from datetime import datetime, date
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from flask_mail import Message
from sqlalchemy import text

# from motracker.extensions import celery, db, filez
from motracker.extensions import csrf_protect, db, mail
from motracker.user.models import User
from motracker.utils import flash_errors, gpx2geo

from .forms import AddFileForm, ApiForm
from .models import ApiKey, Filez, Pointz, Trackz

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
        timez=timez, lat=lat, lon=lon, speed=speed, bearing=bearing, trackdate=trackdate
    )


###########
# MAIN PART
blueprint = Blueprint("gpsdb", __name__, url_prefix="", static_folder="../static")


@blueprint.route("/apikeys", methods=["GET", "POST"])
@login_required
def gpsapi():
    """(re)Generate and/or present API key."""
    form = ApiForm(request.form)
    hasapi = ApiKey.query.filter_by(user_id=current_user.get_id()).all()
    # Handle regeneration of API key
    if request.method == "POST":
        if form.validate_on_submit():
            apikey = strgen.StringGenerator("[\w\d]{10}").render()
            ApiKey.create(user_id=current_user.get_id(), apikey=apikey)
            db.session.commit()
            current_app.logger.info("API key has been added.")
            flash("API key {} has been added.".format(apikey), "info")
            return redirect(url_for("gpsdb.gpsapi"))
        else:
            flash_errors(form)
    # No regeneration request
    apikey = []
    if hasapi:
        for x in hasapi:
            apikey.append(x.apikey)
    db.session.close()
    return render_template("gpsdb/apikey.html", form=form, apikeys=apikey)


@blueprint.route("/apikeys/rm/<string:api>", methods=["GET"])
@login_required
def rmapi(api):
    """RM api key. Everyone logged can remove a key if known."""
    hasapi = ApiKey.query.filter_by(apikey=api).first_or_404(description='There is no data with api key {}'.format(api))
    print(hasapi.apikey)
    db.session.delete(hasapi)
    db.session.commit()
    flash("API key {} has been removed.".format(hasapi.apikey), "warning")
    return redirect(url_for("gpsdb.gpsapi"))


@blueprint.route("/gnss/files", methods=["GET", "POST"])
@login_required
def filezsave():
    """Upload previously recorded tracks."""
    form = AddFileForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Verify if the GPX is valid
            file = request.files["upload_file"]
            try:
                # At the moment we support UTF-8 files and compatible only
                rid = uuid.uuid4()
                parsedfile = file.stream.read().decode("utf-8")
                ourgpx = gpxpy.parse(parsedfile)
                # file is parsing, so we are extracting basic interesting data about it
                length_2d = ourgpx.length_2d()
                length_3d = ourgpx.length_3d()
                moving_time, stopped_time, moving_distance, stopped_distance, max_speed = (
                    ourgpx.get_moving_data()
                )
                uphill, downhill = ourgpx.get_uphill_downhill()
                start_time, end_time = ourgpx.get_time_bounds()
                points_no = len(list(ourgpx.walk(only_points=True)))
            except Exception as e:
                current_app.logger.info(e)
                flash("Uploaded file is not a valid GPX. Try another one.", "warning")
                query = Filez.query.filter_by(user_id=current_user.get_id()).all()
                return render_template("gpsdb/filez.html", allfilez=query, form=form)
            dbfile = Filez.create(
                user_id=current_user.get_id(),
                is_private=form.is_private.data,
                rid=rid,
                description=form.description.data,
            )
            # all tracks are saved with filename which is equal to database ID
            fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(rid) + ".gpx"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(parsedfile)
            fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(rid) + ".txt"
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
            current_app.logger.debug("Saved File: " + str(rid) + ".gpx")
        else:
            flash_errors(form)
    # Present all files belonging to user
    query = Filez.query.filter_by(user_id=current_user.get_id()).all()
    current_app.logger.debug(query)
    gpxq = {}
    for x in query:
        # A brief description presentation
        fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(x.rid) + ".txt"
        with open(fname, "r", encoding="utf-8") as f:
            read_file = f.readlines()
            gpxq[x.id] = read_file
    return render_template("gpsdb/filez.html", allfilez=query, gpxq=gpxq, form=form)


@blueprint.route("/gnss/gpx/<string:gpx_rid>")
def gpxtrace(gpx_rid):
    """Initiates convertion of GPX into our DB and redirects to show GPX on a map."""
    # TODO: use celery to parse the track
    # check if we have the GPS already rendered, if not, render it
    rid = uuid.UUID(gpx_rid)
    track = Trackz.query.filter_by(gpx_rid=rid).first()
    if not track:
        # get username current user
        track_rid = gpx2geo(rid)
    else:
        track_rid = track.rid
    return redirect(url_for("gpsdb.showtrack", track_rid=str(track_rid)))


@blueprint.route("/gnss/tracks/<string:username>")
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
            return render_template("gpsdb/alltracks,html", username=username)
        else:
            return render_template("404.html"), 404


@blueprint.route("/gnss/show/<string:track_rid>")
def showtrack(track_rid):
    """Shows track on the map."""
    # check if track_rid was provided and is an int, else flask sends 404
    if isinstance(track_rid, str):
        rid = uuid.UUID(track_rid)
        # check if track exist
        r1 = Trackz.query.filter_by(rid=rid).first()
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
                        return render_template("404.html"), 404
        else:
            return render_template("404.html"), 404
        return render_template(
            "gpsdb/showtrack.html",
            track_rid=track_rid,
            trackname=trackname,
            trackdesc=trackdesc,
            username=userdb.username,
        )


@blueprint.route("/gnss/realtime/<string:track_rid>")
def realtime(track_rid):
    """Shows realtime position for a track."""
    # TODO: add possibility for a user to hide (s)hes realtime location.
    # check if username was provided and is valid, else flask sends 404.
    if isinstance(track_rid, str):
        rid = uuid.UUID(track_rid)
        # check if track exist
        r1 = Trackz.query.filter_by(rid=rid).first_or_404()
        if r1:
            # check track for username
            userdb = User.query.filter_by(id=r1.user_id).first_or_404()
            return render_template(
                "gpsdb/realtime.html",
                track_rid=track_rid,
                device=r1.device,
                username=userdb.username,
            )


@blueprint.route("/gnss/json/<string:track_rid>/<string:limit>")
def geojson(track_rid, limit):
    """Sends a GeoJSON built from a track."""
    # fake response is the same for all cases
    fakeresponse = current_app.response_class(
        response=faketrack, status=200, mimetype="application/json"
    )
    # check if track_id was provided and is a string, else flask sends 404
    if isinstance(track_rid, str):
        rid = uuid.UUID(track_rid)
        # check if track exist
        r1 = Trackz.query.filter_by(rid=rid).first()
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

        if limit == "0":
            # this version is faster
            sql = text(
                "SELECT ST_AsGeoJSON(subq.*) as geojson FROM (SELECT ST_MakeLine(geom ORDER BY timez)\
                FROM points WHERE track_id = {}) as subq".format(
                r1.id,
            ))
        else:
            # this version is slower
            sql = text("\
                SELECT ST_AsGeoJSON(subq.*) FROM ( \
                    SELECT ST_MakeLine(geom) FROM \
                        (SELECT geom FROM points WHERE points.track_id = {} ORDER BY points.timez DESC LIMIT {}) \
                    AS aliass \
                ) as subq".format(
                    r1.id,
                    limit
                ))
        result = db.session.execute(sql)
        trackjson = result.fetchone()  # TODO: maybe .fetchall() some day?
        current_app.logger.debug(sql)
        current_app.logger.debug(trackjson)
        data = '{"type":"FeatureCollection","features":[' + trackjson[0] + "]}"
        response = current_app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
        )
        db.session.close()
        return response


@blueprint.route("/gnss/jsonp/<int:jtype>/<string:track_rid>")
def geojsonr(jtype, track_rid):
    """Sends a GeoJSON built from a track."""
    # fake response is the same for all cases
    fakeresponse = current_app.response_class(
        response=faketrack, status=200, mimetype="application/json"
    )
    # check if track_rid was provided and is an string, else flask sends 404
    if isinstance(track_rid, str) and isinstance(jtype, int):
        # check if track exist
        rid = uuid.UUID(track_rid)
        r1 = Trackz.query.filter_by(rid=rid).first()
        if r1:
            # check if track was rendered from a GPX, it is not realtime
            if r1.gpx_id:
                return fakeresponse
            # simplifying things, we are showing last recorded position
            # of specified track
            # q2 = Pointz.query.filter_by(track_id=q1.id).order_by(Pointz.timez.desc()).first()
            # q2 = text('SELECT ST_AsGeoJSON(points.geom ORDER BY points.timez DESC,6) \
            #           FROM points WHERE points.track_id = {}'.format(r1.id))
            if jtype > 0 and jtype < 100:
                limit = "LIMIT {}".format(jtype)
            else:
                limit = "LIMIT 1"
            q2 = text(
                "SELECT ST_AsGeoJSON(subq.*) as geojson FROM (SELECT geom,\
                      id, timez, altitude, speed, bearing, sat, comment from \
                      points WHERE track_id = '{}' ORDER BY timez DESC {}) \
                      as subq".format(
                    r1.id, limit
                )
            )
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
                        y += x[0]
                        z += 1
                data = '{"type":"FeatureCollection","features":[' + y + "]}"
                current_app.logger.debug(y)
                response = current_app.response_class(
                    response=data, status=200, mimetype="application/json"
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


@blueprint.route("/gnss/img/<string:track_rid>.svg")
def geosvg(track_rid):
    """Sends a GeoJON built from a track."""
    # fake response is the same for all cases
    fakesvg = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="180">\
        <rect x="50" y="20" rx="20" ry="20" width="150" height="150" style="\
        fill:red;stroke:black;stroke-width:5;opacity:0.5" /></svg>'
    fakeresponse = current_app.response_class(
        response=fakesvg, status=200, mimetype="image/svg+xml"
    )
    # check if track_id was provided and is an int, else flask sends 404
    if isinstance(track_rid, str):
        # check if track exist
        rid = uuid.UUID(track_rid)
        r1 = Trackz.query.filter_by(id=rid).first()
        if not r1:
            # if track does not exist in our database, we are sending a fake one
            # instead of
            return fakeresponse
        # here we ask for a specific track in plain SQL as it is simpler

        # we cut results to 6 decimal places as it gives ~11cm accuracy which is enough - but it does not work as subq?
        sql = text(
            "SELECT ST_AsSVG(ST_MakeLine(ST_Transform(points.geom,4326) ORDER BY points.timez),1,6) \
                FROM points WHERE points.track_id = {};".format(
                track_rid
            )
        )
        result = db.session.execute(sql)
        tracksvg = result.fetchone()  # TODO: maybe .fetchall() some day?
        current_app.logger.debug(tracksvg)
        data = '<svg xmlns="http://www.w3.org/2000/svg">\
            <path d="{}" fill="cadetblue" /></svg>'.format(
            tracksvg[0]
        )
        response = current_app.response_class(
            response=data, status=200, mimetype="image/svg+xml"
        )
        db.session.close()
        return response


@blueprint.route("/gnss/data/opengts")
def opengts():
    """Receives data from OpenGTS compatible receiver device.

    http://www.opengts.org/OpenGTS_Config.pdf
    http://www.geotelematic.com/docs/StatusCodes.pdf
    """
    alt = request.args.get("alt")
    apicode = request.args.get("acct")
    code = request.args.get("code")
    gprmc = request.args.get("gprmc")
    device = request.args.get("id")
    current_app.logger.debug("alt = {}".format(alt))
    current_app.logger.debug("id = {}".format(apicode))
    current_app.logger.debug("code = {}".format(code))
    current_app.logger.debug("device = {}".format(device))
    current_app.logger.debug("gprmc = {}".format(gprmc))

    # parsing id to match GNSS Api
    haskey = ApiKey.query.filter_by(apikey=apicode).first()
    if haskey:
        user_id = haskey.user_id
        current_app.logger.info(
            "Found valid API code belonging to User ID = {}.".format(user_id)
        )
    else:
        current_app.logger.info(
            "No user has such an API key = {}. Ignoring request then.".format(id)
        )
        return "Hello?"

    # code 0xF020 means OpenGTS location reporting
    if code == "0xF020":
        # parsing NMEA-0183 $GPRMC record
        gpsdata = parse_rmc(gprmc)
        current_app.logger.debug("parsed gprmc: {}".format(gpsdata))
        # checking tracks database for the data and device
        trackdb = Trackz.query.filter_by(
            trackdate=gpsdata["trackdate"], device=device
        ).first()
        if trackdb:
            current_app.logger.debug("trackdb: {}".format(trackdb))
        else:
            # we need to create a track
            trackdb = Trackz.create(
                name="OpenGTS",
                user_id=user_id,
                start=datetime.utcnow(),
                description="LiveTracking",
                device=device,
                trackdate=gpsdata["trackdate"],
                rid=uuid.uuid4(),
            )
            current_app.logger.debug("trackdb: {}".format(trackdb))
        # we have track id, now we must check if the location was not already
        # submitted, as it looks like opengts often tries to resubmit the same
        # points over and over again.
        points = Pointz.query.filter_by(
            track_id=trackdb.id,
            geom="SRID=4326;POINT({} {})".format(gpsdata["lon"], gpsdata["lat"]),
            timez=gpsdata["timez"],
        ).first()
        if not points:
            # uff, now we can finally submit location
            points = Pointz.create(
                track_id=trackdb.id,
                geom="SRID=4326;POINT({} {})".format(gpsdata["lon"], gpsdata["lat"]),
                altitude=alt,
                timez=gpsdata["timez"],
                speed=gpsdata["speed"],
                bearing=gpsdata["bearing"],
                comment="OpenGTS",
                sat=None,
                vdop=None,
                pdop=None,
                hdop=None,
                provider="gps",
            )
            # at the end we are updating the track table with current time
            current_app.logger.debug(points)
            trackdb.stop = datetime.utcnow()
            db.session.commit
            db.session.close()
        else:
            current_app.logger.debug("We already have that point recorded. Thank you.")
        #
    return "OK"


@blueprint.route("/client/index.php", methods=["GET", "POST"])
@csrf_protect.exempt
def uloggerlogin():
    """μlogger client compatibility."""
    current_app.logger.debug(request.get_data())
    if request.method == "POST":
        action = request.form["action"]
        if action == "auth":
            # username and password are the same at the moment
            password = request.form["pass"]
            username = request.form["user"]
            # parsing id to match GNSS Api
            haskey = ApiKey.query.filter_by(apikey=password).first()
            if haskey:
                user_id = haskey.user_id
                current_app.logger.info(
                    "Found valid API code belonging to User ID = {}.".format(user_id)
                )
                session["username"] = user_id
                # send a success to the app
                return jsonify(error=False)
            else:
                current_app.logger.info(
                    "No user has such an API key = {}. Ignoring request then.".format(
                        id
                    )
                )
                # send error to the app as we do not have such a user
                return jsonify(error=True, message="go away")
        elif action == "addtrack":
            if "username" in session:
                username = session["username"]
            else:
                current_app.logger.info("Not logged in.")
                return jsonify(error=True, message="go away")
            # adding a new track
            trackname = request.form["track"]
            trackdb = Trackz.create(
                name=trackname,
                user_id=username,
                start=datetime.utcnow(),
                description="LiveTracking",
                device="μlogger",
                trackdate=datetime.utcnow(),
                rid=uuid.uuid4(),
            )
            current_app.logger.debug("trackdb: {}".format(trackdb))
            return jsonify(error=False, trackid=trackdb.id)
        elif action == "addpos":
            if "username" in session:
                username = session["username"]
            else:
                current_app.logger.info("Not logged in.")
                return jsonify(error=True, message="go away")
            # adding new point to existing track
            lat = request.form["lat"]
            lon = request.form["lon"]
            tstamp = datetime.fromtimestamp(int(request.form["time"]))
            trackid = request.form["trackid"]
            try:
                alti = request.form["altitude"]
            except Exception as e:
                alti = 0
                current_app.logger.debug(e)
            try:
                provider = request.form["provider"]
            except Exception as e:
                provider = "unknown"
                current_app.logger.debug(e)
            try:
                accu = request.form["accuracy"]
            except Exception as e:
                accu = "unknown"
                current_app.logger.debug(e)
            # we have track id, now we must check if the location was not already
            # submitted, as it looks like ulogger sometimes tries to resubmit the same
            # points over and over again.
            points = Pointz.query.filter_by(
                track_id=trackid,
                geom="SRID=4326;POINT({} {})".format(lon, lat),
                timez=tstamp,
            ).first()
            if not points:
                # uff, now we can finally submit location
                newpoint = Pointz.create(
                    track_id=trackid,
                    geom="SRID=4326;POINT({} {})".format(lon, lat),
                    altitude=alti,
                    timez=tstamp,
                    provider=provider,
                    comment=accu,
                    speed=0,
                    bearing=0,
                    hdop=0,
                    vdop=0,
                    pdop=0,
                    sat=0,
                )
                if newpoint:
                    current_app.logger.info("New point added: {}".format(newpoint))
                    return jsonify(error=False)
                else:
                    return jsonify(
                        error=True, message="problemz with adding, check the server."
                    )
            else:
                current_app.logger.info(
                    "This point is already added, ignoring: {}".format(points)
                )
                return jsonify(error=False)
            db.session.commit
            db.session.close()


@blueprint.route("/mkr")
@csrf_protect.exempt
def mkr():
    """Receives data from Arduino receiver device, which is my another project.
    """
    # mandatory values
    apicode = request.args.get("apikey")
    device = request.args.get("id")

    # src has two possible values: gps & gsm
    src = request.args.get("src")

    # Building datetime from URI
    gps_day = request.args.get("da")
    gps_month = request.args.get("mo")
    gps_year = request.args.get("ye")
    gps_minute = request.args.get("mi")
    gps_hour = request.args.get("ho")
    gps_second = request.args.get("se")
    gps_datetime_string = "{}-{}-{} {}:{}:{}".format(gps_day, gps_month, gps_year, gps_hour, gps_minute, gps_second)
    gps_datetime = datetime.strptime(gps_datetime_string, "%d-%m-%y %H:%M:%S")
    gps_date = date(int(gps_year), int(gps_month), int(gps_day))

    if src == 'gps':
        lat = float(request.args.get("lat"))/10000000
        lon = float(request.args.get("lon"))/10000000
    else:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

    # optional values:
    if request.args.get("he"):
        gps_head = request.args.get("he")
        if gps_head == "999999.000000":
            gps_head = None
    else:
        gps_head = None

    if request.args.get("alt"):
        gps_alt = request.args.get("alt")
    else:
        gps_alt = None

    if request.args.get("sp"):
        gps_speed = request.args.get("sp")
    else: 
        gps_speed = None

    # current_app.logger.debug("date = {}".format(gps_datetime))

    if request.args.get("sat"):
        gps_sat = request.args.get("sat")
    else:
        gps_sat = None

    # parsing id to match GNSS Api
    haskey = ApiKey.query.filter_by(apikey=apicode).first()
    if haskey:
        user_id = haskey.user_id
        # current_app.logger.debug(
        #    "Found valid API code belonging to User ID = {}.".format(user_id)
        # )
    else:
        current_app.logger.info(
            "No user has such an API key = {}. Ignoring request then.".format(id)
        )
        return "Hello?"

    # checking tracks database for the data and device
    trackdb = Trackz.query.filter_by(
        trackdate=gps_date, device=device
    ).first()
    if trackdb:
        # current_app.logger.debug("trackdb: {}".format(trackdb))
        pass
    else:
        # we need to create a track
        trackdb = Trackz.create(
            name="Arduino",
            user_id=user_id,
            start=datetime.utcnow(),
            description="LiveTracking",
            device=device,
            trackdate=gps_date,
            rid=uuid.uuid4(),
        )
    #current_app.logger.debug("trackdb: {}".format(trackdb))

    # we have track id, now we must check if the location was not already
    # submitted, as it looks like opengts often tries to resubmit the same
    # points over and over again.
    points = Pointz.query.filter_by(
        track_id=trackdb.id,
        geom="SRID=4326;POINT({} {})".format(lon, lat),
        timez=gps_datetime,
    ).first()
    if not points:
        # uff, now we can finally submit location
        points = Pointz.create(
            track_id=trackdb.id,
            geom="SRID=4326;POINT({} {})".format(lon, lat),
            altitude=gps_alt,
            timez=gps_datetime,
            speed=gps_speed,
            bearing=gps_head,
            comment=device,
            sat=gps_sat,
            vdop=None,
            pdop=None,
            hdop=None,
            provider=src
        )
        # at the end we are updating the track table with current time
        current_app.logger.debug(points)
        trackdb.stop = datetime.utcnow()

        # send pubsub to redis channel
        reddy = redis.Redis(host='localhost', port=6379, db=3)
        r = reddy.publish("{}".format(trackdb.rid), 'UP')
        current_app.logger.debug("redis publish on {}: {}".format(trackdb.rid, r))

        # closing db access
        db.session.commit
        db.session.close()

    else:
        current_app.logger.debug("We already have that point recorded. Thank you.")

    # we are done.
    return "OK"


@blueprint.route("/sms", methods=["POST"])
@csrf_protect.exempt
def smstext():
    """sms handling, we want to forward all text messagess to email."""
    data = json.loads(request.data)
    current_app.logger.debug(data)

    # we can receive messages in UCS2 so we try to decode them
    message = "{}".format( data['text'] )
    messageclean = re.sub( '\W+','', data['text'] )
    try:
        czyucs = binascii.unhexlify(messageclean).decode('utf-16-be')
        message += "\n\n"
        message += czyucs
    except Exception as e:
        current_app.logger.info(e)

    msg = Message(
            "Arduino SMS from {}".format(data['number']),
            sender='motracker@random.re',
            )
    msg.add_recipient("motracker@random.re")
    msg.body = "{}".format(message)
    mail.send(msg)

    return "OK"

# vim: tabstop=4 shiftwidth=4 expandtab
