from flask import render_template, redirect, url_for
from flask_login import login_required
from app.main import bp


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('/dashboard/'))

