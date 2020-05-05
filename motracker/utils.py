# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from datetime import datetime

import gpxpy
from flask import current_app, flash
from flask_login import current_user
from sqlalchemy import text

from motracker.extensions import db
from motracker.gpsdb.models import Pointz, Trackz

# from motracker.user.models import User

# fakesvg is presented when needed in other functions
fakesvg = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="180">\
           <rect x="50" y="20" rx="20" ry="20" width="150" height="150" style="\
           fill:red;stroke:black;stroke-width:5;opacity:0.5" /></svg>'


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash("{0} - {1}".format(getattr(form, field).label.text, error), category)


# @celery.task(bind=True)
# def gpx2geo(self, gpx_id):
def gpx2geo(gpx_id):
    """Imports a GPX track into our database."""
    fname = current_app.config["UPLOADS_DEFAULT_DEST"] + str(gpx_id) + ".gpx"
    gpx_file = open(fname, "r", encoding="utf-8")
    gpx = gpxpy.parse(gpx_file)
    """  It behaves like that:
    gpxtxt = ""
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                gpxtxt += 'Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation)
    for waypoint in gpx.waypoints:
        gpxtxt += 'waypoint {0} -> ({1},{2})'.format(waypoint.name, waypoint.latitude, waypoint.longitude)
    for route in gpx.routes:
        gpxtxt += 'Route:'
        for point in route.points:
            gpxtxt += 'Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation)
    """
    # Create track in db
    newtrack = Trackz.create(
        user_id=current_user.get_id(),
        name="GPX",
        description="Rendered file {}.gpx".format(gpx_id),
        start=datetime.utcnow(),
        gpx_id=gpx_id,
        device=gpx.creator,
    )
    # Create all points
    for track in gpx.tracks:
        for segment in track.segments:
            for point_no, point in enumerate(segment.points):
                if point.speed is not None:
                    speed = point.speed
                elif point_no > 0:
                    speed = point.speed_between(segment.points[point_no - 1])
                else:
                    speed = 0
                Pointz.create(
                    track_id=newtrack.id,
                    provider=point.source,
                    geom="SRID=4326;POINT({} {})".format(
                        point.longitude, point.latitude
                    ),
                    altitude=point.elevation,
                    timez=point.time,
                    speed=speed,
                    bearing=point.course,
                    sat=point.satellites,
                    hdop=point.horizontal_dilution,
                    vdop=point.vertical_dilution,
                    pdop=point.position_dilution,
                    comment="",
                )
    # TODO add finished datetime.utcnow() to stop
    return newtrack.id


def track2svgline(track_id):
    """Prepares an SVG overview built from a track."""
    # check if track exist
    r1 = Trackz.query.filter_by(id=track_id).first()
    if not r1:
        return fakesvg
    else:
        # we cut results to 6 decimal places as it gives ~11cm accuracy which is enough
        sql = text(
            "SELECT ST_AsSVG(ST_MakeLine(ST_Transform(points.geom,4326) ORDER BY points.timez),1,6) \
                FROM points WHERE points.track_id = {};".format(
                track_id
            )
        )
        result = db.session.execute(sql)
        tracksvg = result.fetchone()
        current_app.logger.debug(tracksvg)
        data = '<svg xmlns="http://www.w3.org/2000/svg">\
                <path d="{}" fill="cadetblue" /></svg>'.format(
            tracksvg[0]
        )
        db.session.close()
        return data


def track2svgpoints(track_id):
    """Prepares an SVG overview built from a track."""
    # check if track exist
    r1 = Trackz.query.filter_by(id=track_id).first()
    if not r1:
        return fakesvg
    else:
        data = '<svg xmlns="http://www.w3.org/2000/svg">'
        sql = text(
            "SELECT ST_AsSVG(geom) FROM points WHERE points.track_id = {};".format(
                track_id
            )
        )
        result = db.session.execute(sql)
        tracksvg = result.fetchall()
        current_app.logger.debug(tracksvg)
        for x in tracksvg:
            data += '<circle {} r="0.0001" />'.format(x[0])
        data += "</svg>"
        current_app.logger.debug(data)
        return data

def track_live(user_id):
    """Checks if  user has live tracks atm."""

    sql = text(
        "SELECT * from tracks WHERE user_id = {} AND date(start) = '{}'".format(
            user_id,
            datetime.utcnow().date()
        ))
    #current_app.logger.debug(sql)
    result = db.session.execute(sql)
    trackdb = result.fetchall()
    #current_app.logger.debug(trackdb)
    lasttrack = trackdb[0]
    #current_app.logger.debug(lasttrack)
    return lasttrack.rid
