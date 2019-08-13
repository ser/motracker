# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from datetime import datetime

import gpxpy
from flask import current_app, flash
from flask_login import current_user

from motracker.gpsdb.models import Pointz, Trackz
from motracker.user.models import User


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
    gpx_file = open(fname, 'r', encoding="utf-8")
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
        device=gpx.creator
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
                    geom='SRID=4326;POINT({} {})'.format(point.longitude, point.latitude),
                    altitude=point.elevation,
                    timez=point.time,
                    speed=speed,
                    bearing=point.course,
                    sat=point.satellites,
                    hdop=point.horizontal_dilution,
                    vdop=point.vertical_dilution,
                    pdop=point.position_dilution,
                    comment=""
                )
    # TODO add finished datetime.utcnow() to stop
    return(newtrack.id)
