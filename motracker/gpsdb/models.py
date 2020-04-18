# -*- coding: utf-8 -*-
"""GPS tracks and API models."""

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID

from motracker.database import (
    Column,
    Model,
    SurrogatePK,
    db,
    reference_col,
    relationship,
)


class ApiKey(SurrogatePK, Model):
    """Key for feeding data."""

    __tablename__ = "apikey"
    apikey = Column(db.String(10), unique=True, nullable=False)
    user_id = reference_col("users", nullable=False)
    #$user = relationship("User", cascade="all,delete", backref="apiusers")

    def __init__(self, apikey, **kwargs):
        """Create instance."""
        db.Model.__init__(self, apikey=apikey, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<ApiKey({apikey})>".format(apikey=self.apikey)


# class SMS(SurrogatePK, Model):
#    """SMS (optional, not documented!)."""
#
#    __tablename__ = "sms"
#    number = Column(db.String(20), unique=False, nullable=False)
#    sms = db.Column(db.String, unique=False, nullable=False)
#
#    def __init__(self, number, sms, **kwargs):
#        """Create instance."""
#        db.Model.__init__(self, number=number, sms=sms, **kwargs)
#
#    def __repr__(self):
#        """Represent instance as a unique string."""
#        return "<Number: {}, sms: {}".format(self.number, self.sms)


class Filez(SurrogatePK, Model):
    """Table with uploaded raw GPX files."""

    __tablename__ = "files"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", cascade="all,delete", backref="fileusers")
    when_uploaded = Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, nullable=True)
    rid = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    description = db.Column(db.String, nullable=False)

    def __init__(self, is_private, description, rid, **kwargs):
        """Create instance."""
        db.Model.__init__(
            self, is_private=is_private, description=description, rid=rid, **kwargs
        )

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<id: {}, desc: {}, when: {}>".format(
            self.id, self.description, self.rid, self.when_uploaded
        )


class Trackz(SurrogatePK, Model):
    """Table with tracks."""

    __tablename__ = "tracks"
    name = Column(db.String(255), unique=False, nullable=False)
    device = Column(db.String(255), unique=False, nullable=False)
    trackdate = Column(db.Date(), nullable=True)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", cascade="all,delete", backref="trackusers")
    start = Column(db.DateTime(), nullable=True)
    stop = Column(db.DateTime(), nullable=True)
    description = db.Column(db.String, nullable=True)
    rid = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    gpx_id = reference_col("files", nullable=True)

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<Trackz({name})>".format(name=self.name)


class Pointz(SurrogatePK, Model):
    """Table with points.

    Postgis allows 3D points, but because our maps are displayed in 2D, we do
    not need to use that possibility. It will give no advantage, slowing down
    the index.
    """

    __tablename__ = "points"
    timez = Column(db.DateTime(), nullable=False)
    track_id = reference_col("tracks", nullable=True)
    track = relationship("Trackz", cascade="all,delete", backref="tracks")
    geom = Column(
        Geometry("POINT", dimension=2, srid=4326, management=True),
        unique=False,
        nullable=True,
    )
    altitude = Column(db.Float, unique=False, nullable=True)
    speed = Column(db.Float, unique=False, nullable=True)
    bearing = Column(db.Float, unique=False, nullable=True)
    hdop = Column(db.Float, unique=False, nullable=True)
    vdop = Column(db.Float, unique=False, nullable=True)
    pdop = Column(db.Float, unique=False, nullable=True)
    sat = Column(db.Integer, unique=False, nullable=True)
    provider = Column(db.String(100), unique=False, nullable=True)
    comment = Column(db.String(255), unique=False, nullable=True)

    def __init__(
        self,
        timez,
        track_id,
        geom,
        altitude,
        speed,
        bearing,
        sat,
        hdop,
        vdop,
        pdop,
        provider,
        comment,
    ):
        """Create instance."""
        db.Model.__init__(
            self,
            timez=timez,
            track_id=track_id,
            geom=geom,
            altitude=altitude,
            speed=speed,
            bearing=bearing,
            hdop=hdop,
            vdop=vdop,
            pdop=pdop,
            sat=sat,
            provider=provider,
            comment=comment,
        )

    def __repr__(self):
        """Represent instance as a unique string."""
        return "timez: {}, track_id: {}, geom: {}, altitude: {}, \
speed: {}, bearing: {}, hdop: {}, vdop: {}, pdop: {}, sat: {}, \
provider: {}, comment: {}".format(
            self.timez,
            self.track_id,
            self.geom,
            self.altitude,
            self.speed,
            self.bearing,
            self.hdop,
            self.vdop,
            self.pdop,
            self.sat,
            self.provider,
            self.comment,
        )
