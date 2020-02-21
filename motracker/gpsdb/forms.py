# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import BooleanField, FileField, StringField
from wtforms.validators import DataRequired, InputRequired

from motracker.extensions import filez


class ApiForm(FlaskForm):
    """Change API key form."""

    confirm = BooleanField(
        "If you want to re-generate the key, select this checkbox to confirm",
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ApiForm, self).__init__(*args, **kwargs)
        # self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(ApiForm, self).validate()
        if not initial_validation:
            return False
        return True


class AddFileForm(FlaskForm):
    """Add GPX file."""

    description = StringField("GPX File Description", validators=[DataRequired()])
    is_private = BooleanField("Do you want to keep this file privately?")
    upload_file = FileField(
        "Chose File",
        # validators=[FileRequired(), FileAllowed(filez, 'GPX tracks onlY!')]
        validators=[FileRequired()],
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(AddFileForm, self).__init__(*args, **kwargs)

    def validate(self):
        """Validate the form."""
        initial_validation = super(AddFileForm, self).validate()
        if not initial_validation:
            return False
        return True
