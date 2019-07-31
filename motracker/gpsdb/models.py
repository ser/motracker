# -*- coding: utf-8 -*-
"""GPS tracks and API models."""

from datetime import datetime

from geoalchemy2 import Geometry

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
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="apikeys")

    def __init__(self, apikey, **kwargs):
        """Create instance."""
        db.Model.__init__(self, apikey=apikey, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<ApiKey({apikey})>".format(apikey=self.apikey)


class Filez(SurrogatePK, Model):
    """Table with uploaded raw GPX files."""

    __tablename__ = "files"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="files")
    is_public = db.Column(db.Boolean, nullable=False)
    description = db.Column(db.String, nullable=False)

    def __init__(self, is_public, description, **kwargs):
        """Create instance."""
        db.Model.__init__(self, is_public=is_public, description=description, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<id: {}>'.format(self.id)


class Trackz(SurrogatePK, Model):
    """Table with tracks."""

    __tablename__ = "tracks"
    name = Column(db.String(255), unique=False, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="tracks")

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<Trackz({name})>".format(name=self.name)


class Pointz(SurrogatePK, Model):
    """Table with points."""

    __tablename__ = "points"
    timez = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    track_id = reference_col("tracks", nullable=True)
    track = relationship("Trackz", backref="points")
    geom = Column(Geometry('POINT'), unique=False, nullable=True)
    altitude = Column(db.Float, unique=False, nullable=True)
    speed = Column(db.Float, unique=False, nullable=True)
    bearing = Column(db.Float, unique=False, nullable=True)
    accuracy = Column(db.Integer, unique=False, nullable=True)
    provider = Column(db.String(100), unique=False, nullable=True)
    comment = Column(db.String(255), unique=False, nullable=True)

    def __init__(self, timez, track_id, track, geom, altitude, speed, bearing,
                 accuracy, provider, comment):
        """Create instance."""
        db.Model.__init__(
            self,
            timez=timez,
            track_id=track_id,
            track=track,
            geom=geom,
            altitude=altitude,
            speed=speed,
            bearing=bearing,
            accuracy=accuracy,
            provider=provider,
            comment=comment
        )

    def __repr__(self):
        """Represent instance as a unique string."""
        return 'timez: {}, track_id: {}, track: {}, geom: {}, altitude: {}, \
    speed: {}, bearing: {}, accuracy: {}, provider: {}, comment: {}'.format(
            self.timez,
            self.track_id,
            self.track,
            self.geom,
            self.altitude,
            self.speed,
            self.bearing,
            self.accuracy,
            self.provider,
            self.comment
        )
