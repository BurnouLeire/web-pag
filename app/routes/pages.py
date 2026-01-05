from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
def login():
    return render_template("login.html")

@bp.route("/")
def dashboard():
    return render_template("dashboard.html")

@bp.route("/")
def laboratorio():
    return render_template("laboratorio.html")
