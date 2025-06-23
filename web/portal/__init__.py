import os
import logging
from flask import Flask
import json
from jinja_markdown import MarkdownExtension

import requests

from portal.decorators import authenticated
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, redirect, url_for, session
from flask_dance.contrib.github import make_github_blueprint, github


__author__ = 'LSSTDESC SRV  <lsstdesc@gmail.com>'


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["GITHUB_OAUTH_CLIENT_ID"] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
app.config["GITHUB_OAUTH_CLIENT_SECRET"] = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")

app.config.from_pyfile('portal.conf')

app.jinja_env.add_extension('jinja_markdown.MarkdownExtension')
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1
)


github_bp = make_github_blueprint(scope="read:org")
app.register_blueprint(github_bp, url_prefix="/github_login")

@app.route("/")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    return "You are @{login} on GitHub".format(login=resp.json()["login"])



@app.route("/logout")
@authenticated
def logout():
    # remove the username from the session if it's there
    if github_bp.token:
        del github_bp.token
    session.clear()
    return redirect(url_for('github_login'))

@app.route('/unauthorized')
def unauthorized():
    return "You are not authorized to view this page (not a member of the LSSTDESC organization)."


@app.route('/dashboard')
def dashboard():
    app.logger.setLevel(logging.DEBUG)
    github_access_token = session.get('github_oauth_token') # Get token from session
    target_org = 'LSSTDESC' # Replace with the organization name

    if github_access_token and is_user_in_org(github_access_token, target_org):
        return "Welcome, you are a member of the organization!"
    if is_user_in_org(github_access_token, target_org):
        return "Welcome, no access token!"
    else:
        return redirect(url_for('unauthorized'))


def is_user_in_org(access_token, organization_name):
    response = github.get("/user/orgs")
    #app.logger.info("Scopes: " + response.headers.get("X-OAuth-Scopes"))

    name = github.get("/user")
    assert name.ok

    userindesc = github.get("/orgs/LSSTDESC/members/" + name.json()["login"])
    if userindesc.ok:
        return True

    #if response.status_code == 200:
    if response.ok:
        organizations = response.json()
        #app.logger.info("query response "+json.dumps(organizations))
        num = len(organizations)
        #app.logger.info("got orgs "+ str(num))
        #app.logger.info("name " + name.json()["login"])
        #app.logger.info("json " + json.dumps(organizations))
        for org in organizations:
        #    app.logger.info("cur org " + org['login'])
            if org['login'] == "LSSTDESC":
                return True
        return False
    else:
        # Handle API error (e.g., invalid token, rate limit exceeded)
        print(f"Error fetching organizations: {response.status_code} - {response.text}")
        return False


