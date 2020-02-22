# -*- coding: utf-8 -*-
"""Click commands."""
import os
from glob import glob
from subprocess import call

import click
from flask.cli import with_appcontext

# from motracker.app import create_app
from motracker.extensions import db

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, "tests")


@click.command()
@click.option("-ma", "--makeadmin", default=None, type=str, help="Set username as admin")
@click.option("-ra", "--removeadmin", default=None, type=str, help="remove username as admin")
@click.option("-sn", "--setname", nargs=2, default=None, type=str, help="setname")
@click.option("-ss", "--setsurname", nargs=2, default=None, type=str, help="setname")
@with_appcontext
def users(makeadmin, removeadmin, setname, setsurname):
    """Sets user actions."""
    if makeadmin:
        sql = "SELECT * FROM users WHERE username='{}'".format(makeadmin)
        result = db.session.execute(sql)
        onerow = result.fetchone()
        if onerow.username and onerow.is_admin is not True:
            sql = "UPDATE users SET is_admin=True WHERE username='{}'".format(makeadmin)
            result = db.session.execute(sql)
            db.session.commit()
            click.echo("{} set correctly as admin.".format(makeadmin))
        else:
            click.echo("is already an admin or does not exist")
    if removeadmin:
        sql = "SELECT * FROM users WHERE username='{}'".format(removeadmin)
        result = db.session.execute(sql)
        onerow = result.fetchone()
        if onerow.username and onerow.is_admin is True:
            sql = "UPDATE users SET is_admin=False WHERE username='{}'".format(removeadmin)
            result = db.session.execute(sql)
            db.session.commit()
            click.echo("{} correctly removed admin rights.".format(removeadmin))
        else:
            click.echo("is not already an admin or does not exist")
    if setname:
        sql = "SELECT * FROM users WHERE username='{}'".format(setname[0])
        result = db.session.execute(sql)
        onerow = result.fetchone()
        if onerow.username:
            sql = "UPDATE users SET first_name='{}' WHERE username='{}'".format(setname[1], setname[0])
            result = db.session.execute(sql)
            db.session.commit()
            click.echo("{} is now {}".format(setname[0], setname[1]))
        else:
            click.echo("I can't understand this: {}".format(setname))
    if setsurname:
        sql = "SELECT * FROM users WHERE username='{}'".format(setsurname[0])
        result = db.session.execute(sql)
        onerow = result.fetchone()
        if onerow.username:
            sql = "UPDATE users SET last_name='{}' WHERE username='{}'".format(setsurname[1], setsurname[0])
            result = db.session.execute(sql)
            db.session.commit()
            click.echo("{} is now {}".format(setsurname[0], setsurname[1]))
        else:
            click.echo("I can't understand this: {}".format(setsurname))
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
