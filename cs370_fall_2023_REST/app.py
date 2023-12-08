from flask import Flask,render_template,request, redirect, url_for, g
from flask_json import FlaskJSON, JsonError, json_response, as_json
import jwt

import sys
import datetime
import bcrypt
import traceback
import sqlite3

# Comment out when running app.py with no headband, Traceback error.
# from tools.eeg import get_head_band_sensor_object

from db_con import get_db_instance, get_db

from tools.token_required import token_required

#used if you want to store your secrets in the aws valut
#from tools.get_aws_secrets import get_secrets

from tools.logging import logger

ERROR_MSG = "Ooops.. Didn't work!"


#Create our app
app = Flask(__name__)
#add in flask json
FlaskJSON(app)

#g is flask for a global var storage 
def init_new_env():
    #To connect to DB
    if 'db' not in g:
        g.db = get_db()

    if 'hb' not in g:
        g.hb = get_head_band_sensor_object()

    #g.secrets = get_secrets()
    #g.sms_client = get_sms_client()

#This gets executed by default by the browser if no page is specified
#So.. we redirect to the endpoint we want to load the base page
@app.route('/') #endpoint
def index():
    return redirect('/static/index.html')

@app.route("/secure_api/<proc_name>",methods=['GET', 'POST'])
@token_required
def exec_secure_proc(proc_name):
    logger.debug(f"Secure Call to {proc_name}")

    #setup the env
    init_new_env()

    #see if we can execute it..
    resp = ""
    try:
        fn = getattr(__import__('secure_calls.'+proc_name), proc_name)
        resp = fn.handle_request()
    except Exception as err:
        ex_data = str(Exception) + '\n'
        ex_data = ex_data + str(err) + '\n'
        ex_data = ex_data + traceback.format_exc()
        logger.error(ex_data)
        return json_response(status_=500 ,data=ERROR_MSG)

    return resp



@app.route("/open_api/<proc_name>",methods=['GET', 'POST'])
def exec_proc(proc_name):
    logger.debug(f"Call to {proc_name}")

    #setup the env
    init_new_env()

    #see if we can execute it..
    resp = ""
    try:
        fn = getattr(__import__('open_calls.'+proc_name), proc_name)
        resp = fn.handle_request()
    except Exception as err:
        ex_data = str(Exception) + '\n'
        ex_data = ex_data + str(err) + '\n'
        ex_data = ex_data + traceback.format_exc()
        logger.error(ex_data)
        return json_response(status_=500 ,data=ERROR_MSG)

    return resp

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Retrieves the user data
    name = data['name'] 
    dob = data['dob'] 
    gender = data['gender']
    email = data['email']
    
    # Connects to the database and save the user's information.
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(''' INSERT INTO users (name, dob, gender, email)
                    VALUES (?,?,?,?)''', (name, dob, gender, email))
    conn.commit()
    conn.close()
    print('The user data has been saved to the database.')     
    
    return json_response(status_=200 ,data="Success")

if __name__ == '__main__':
    # Create the user database if doesn't exist
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(''' CREATE TABLE IF NOT EXISTS users(
                    email TEXT PRIMARY KEY, 
                    name text NOT NULL,
                    dob DATE NOT NULL, 
                    gender TEXT NOT NULL
                )''')
    conn.close()
    
    app.run(host='0.0.0.0', port=80)

