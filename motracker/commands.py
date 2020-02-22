# -*- coding: utf-8 -*-
"""Click commands."""
import click
import os
from flask import current_app
from flask.cli import with_appcontext
from glob import glob
from subprocess import call

#from motracker.app import create_app
from motracker.extensions import db

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, "tests")


@click.command()
@click.option(
    "-ma",
    "--makeadmin",
    default=None,
    help="Set username as admin",
)
@with_appcontext
def users(makeadmin):
    """Sets user actions."""
    sql = "SELECT * FROM users WHERE username='{}'".format(makeadmin)
    result = db.session.execute(sql)
    onerow = result.fetchone()
    if onerow.username and onerow.is_admin is not True:
        sql = "UPDATE users SET is_admin=True WHERE username='{}'".format(makeadmin)
        result = db.session.execute(sql)
        db.session.commit()
        print("{} set correctly as admin.".format(makeadmin))
    else:
        print("is already an admin or does not exist")
    db.session.close()


@click.command()
def test():
    """Run the tests."""
    import pytest

    rv = pytest.main([TEST_PATH, "--verbose"])
    exit(rv)


@click.command()
@click.option(
    "-f",
    "--fix-imports",
    default=True,
    is_flag=True,
    help="Fix imports using isort, before linting",
)
@click.option(
    "-c",
    "--check",
    default=False,
    is_flag=True,
    help="Don't make any changes to files, just confirm they are formatted correctly",
)
def lint(fix_imports, check):
    """Lint and check code style with black, flake8 and isort."""
    skip = ["node_modules", "requirements", "migrations"]
    root_files = glob("*.py")
    root_directories = [
        name for name in next(os.walk("."))[1] if not name.startswith(".")
    ]
    files_and_directories = [
        arg for arg in root_files + root_directories if arg not in skip
    ]

    def execute_tool(description, *args):
        """Execute a checking tool with its arguments."""
        command_line = list(args) + files_and_directories
        click.echo("{}: {}".format(description, " ".join(command_line)))
        rv = call(command_line)
        if rv != 0:
            exit(rv)

    isort_args = ["-rc"]
    black_args = []
    if check:
        isort_args.append("-c")
        black_args.append("--check")
    if fix_imports:
        execute_tool("Fixing import order", "isort", *isort_args)
    execute_tool("Formatting style", "black", *black_args)
    execute_tool("Checking code style", "flake8")
