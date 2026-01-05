from flask import Blueprint, render_template, redirect, url_for, request

bp = Blueprint("auth", __name__)

@bp.route("/")
@bp.route("/login")
def login():
    return render_template("login.html")