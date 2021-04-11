from flask import Flask, render_template, redirect, request, jsonify, session, url_for

from secrets import token_urlsafe
import json
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(16)

config={}
with open('config.json', 'r') as f:
    config = json.load(f)

def generateChallenge():
    token = token_urlsafe(100)
    return token[:128]

def getAccessToken():
    url = f'https://myanimelist.net/v1/oauth2/token'
    payload = {
        "client_id" : config["CLIENT_ID"],
        "code" : session["CODE"],
        "code_verifier" : session["CODE_VERIFIER"],
        "grant_type" : "authorization_code"
    }
    response = requests.post(url, payload).json()
    return response

def refreshAccessToken():
    url = f'https://myanimelist.net/v1/oauth2/token'
    payload = {
        "client_id" : config["CLIENT_ID"],
        "grant_type" : "refresh_token",
        "refresh_token" : session["ACCESS_TOKEN"]["refresh_token"]
    }
    response = requests.post(url, payload).json()
    session["ACCESS_TOKEN"] = response

def makeApiGetRequest(url):
    authHeader = {
        "Authorization" : f"Bearer {session['ACCESS_TOKEN']['access_token']}"
    }
    response = requests.get(url, headers=authHeader)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        refreshAccessToken()
        return makeApiGetRequest()

@app.route('/')
def index():
    if "ACCESS_TOKEN" in session:
        url = 'https://api.myanimelist.net/v2/users/@me'
        response = makeApiGetRequest(url)
        return render_template('index.html', userData=response)
    else: return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    code_challenge = generateChallenge()
    session["CODE_VERIFIER"] = code_challenge

    url = f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={config["CLIENT_ID"]}&code_challenge={session["CODE_VERIFIER"]}&state=RequestID'
    return redirect(url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/oauth')
def oauth():
    session["CODE"] = request.args.get('code')

    access_token = getAccessToken()
    session["ACCESS_TOKEN"] = access_token

    return redirect(url_for('index'))

@app.route('/me')
def userData():
    url = 'https://api.myanimelist.net/v2/users/@me'
    response = makeApiGetRequest(url)

    return render_template('user.html', userData=response)

@app.route('/myAnimeList')
def myAnimeList():
    url = 'https://api.myanimelist.net/v2/users/@me/animelist?limit=1000'
    response = makeApiGetRequest(url)

    return render_template('animeList.html', animeList=response['data'])
    # return jsonify(response)

@app.route('/sessionStuff')
def sessionData():
    sessionDict = {}
    for item in list(session.keys()):
        sessionDict[item] = session[item]
    # return render_template('session.html', sessionData)
    return jsonify(sessionDict)