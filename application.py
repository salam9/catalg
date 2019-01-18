from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import make_response, flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Company, Phone, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from sqlalchemy.orm.exc import NoResultFound
from functools import wraps
import random
import httplib2
import json
import requests
import os
import ssl
import string

app = Flask(__name__)

engine = create_engine('sqlite:///phonemakers.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Phone Makers Application"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                   json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; ' \
              'height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/disconnect')
def disconnect():
    if 'username' in login_session:
        gdisconnect()
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        return response
    else:
        response = make_response(
                    json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/company/<int:company_id>/phone/JSON')
@app.route('/company/<int:company_id>/JSON')
def companyJSON(company_id):
    company = session.query(Company).filter_by(id=company_id).one()
    phones = session.query(Phone).filter_by(company_id=company_id).all()
    return jsonify(phones=[i.serialize for i in phones])


@app.route('/company/<int:company_id>/phone/<int:phone_id>/JSON')
@app.route('/company/<int:company_id>/<int:phone_id>/JSON')
def phoneJSON(company_id, phone_id):
    phone = session.query(Phone).filter_by(id=phone_id).one()
    return jsonify(phone=phone.serialize)


@app.route('/Companies/JSON')
def companiesJSON():
    companies = session.query(Company).all()
    return jsonify(companies=[i.serialize for i in companies])


@app.route('/')
@app.route('/Companies')
def showCompanies():
    companies = session.query(Company).all()
    phones = session.query(Phone).order_by(Phone.id.desc()).limit(6)
    return render_template(
                'Companies.html', categories=companies, items=phones)


@app.route('/company/<int:company_id>/')
@app.route('/company/<int:company_id>/phones/')
def showCompany(company_id):
    company = session.query(Company).filter_by(id=company_id).one()
    phones = session.query(Phone).filter_by(company_id=company.id).all()
    if 'username' not in login_session:
        return render_template(
                    'publicCompany.html',  company=company, items=phones)
    else:
        return render_template('Company.html', company=company, items=phones)


@app.route('/company/<int:company_id>/<int:phone_id>/')
@app.route('/company/<int:company_id>/phone/<int:phone_id>/')
def showPhone(company_id, phone_id):
    phone = session.query(Phone).filter_by(id=phone_id).one()
    return render_template('phonedetails.html', item=phone)


@app.route('/company/<int:company_id>/new', methods=['GET', 'POST'])
@login_required
def createPhone(company_id):
    if request.method == 'POST':
        newPhone = Phone(
                    name=request.form['name'],
                    modelNo=request.form['modelNo'],
                    price=request.form['price'],
                    company_id=company_id,
                    user_id=login_session['user_id'])
        session.add(newPhone)
        session.commit()
        flash("new Phone created!")
        return redirect(url_for('showCompany', company_id=company_id))
    else:
        return render_template('addPhone.html', company_id=company_id)


@app.route(
    '/company/<int:company_id>/<int:phone_id>/delete', methods=['GET', 'POST'])
@app.route(
    '/company/<int:company_id>/phone/<int:phone_id>/delete',
    methods=['GET', 'POST'])
@login_required
def deletePhone(company_id, phone_id):
    deletedPhone = session.query(Phone).filter_by(id=phone_id).one_or_none()
    if deletedPhone.user_id != login_session['user_id']:
        return """<script>function myFunction() \
                {alert('You are not authorized to delete this phone.');}\
                </script><body onload= 'myFunction()' >"""
    if request.method == 'POST':
        session.delete(deletedPhone)
        flash('%s Successfully Deleted' % deletedPhone.name)
        session.commit()
        return redirect(url_for('showCompany', company_id=company_id))
    else:
        return render_template('deletePhone.html', phone=deletedPhone)


@app.route(
    '/company/<int:company_id>/<int:phone_id>/edit', methods=['GET', 'POST'])
@app.route(
    '/company/<int:company_id>/phone/<int:phone_id>/edit',
    methods=['GET', 'POST'])
@login_required
def editPhone(company_id, phone_id):
    editedPhone = session.query(Phone).filter_by(id=phone_id).one()
    if editedPhone.user_id != login_session['user_id']:
        return """<script>function myFunction() \
                {alert('You are not authorized to edit this phone')} \
                </script><body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['name']:
            editedPhone.name = request.form['name']
        if request.form['modelNo']:
            editedPhone.modelNo = request.form['modelNo']
        if request.form['price']:
            editedPhone.price = request.form['price']
        session.add(editedPhone)
        session.commit()
        flash("Phone updated!", 'success')
        return redirect(url_for('showCompany', company_id=company_id))
    else:
        return render_template(
                'editphone.html',
                company_id=company_id,
                phone_id=phone_id,
                phone=editedPhone)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
