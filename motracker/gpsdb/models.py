# -*- coding: utf-8 -*-
"""GPS tracks and api models."""

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
