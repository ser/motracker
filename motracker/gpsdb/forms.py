# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms.validators import DataRequired, EqualTo, InputRequired

class ApiForm(FlaskForm):
    """Change API key form."""

    confirm = BooleanField(
        "If you want to re-generate the key, select this checkbox to confirm",
        validators=[DataRequired(), InputRequired(), EqualTo(True, "You must confirm that you want to change the API key")]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ApiForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(ApiForm, self).validate()
        if not initial_validation:
            return False
