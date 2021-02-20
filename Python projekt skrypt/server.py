from io import BytesIO
import logging
import flask
import json
import httplib2
import time
import webbrowser
import requests
import urllib.request
import pandas as pd
from datetime import datetime
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from datetime import timedelta


app = flask.Flask(__name__)

CLIENT_ID = '595779153213-n0he2h9e82h4dd5bs3mfl99gji1mgsde.apps.googleusercontent.com'
CLIENT_SECRET = 'jDqdpHXf-pVXPxpjpKMLFNkO'
Sdate = str((datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d"))
OAUTH_SCOPE = 'https://www.googleapis.com/auth/fitness.activity.read https://www.googleapis.com/auth/fitness.blood_glucose.read https://www.googleapis.com/auth/fitness.blood_pressure.read https://www.googleapis.com/auth/fitness.body_temperature.read https://www.googleapis.com/auth/fitness.location.read https://www.googleapis.com/auth/fitness.nutrition.read https://www.googleapis.com/auth/fitness.oxygen_saturation.read https://www.googleapis.com/auth/fitness.body.read https://www.googleapis.com/auth/fitness.reproductive_health.read'
DATA_SOURCE = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"

now = datetime.now()-timedelta(days=1)
to_day=(datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
last_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
T_y_mid= int(time.mktime(last_day.timetuple())) * 1000000000
T_T_mid= int(time.mktime(to_day.timetuple())) * 1000000000
T_now= int(time.mktime(datetime.now().timetuple())) * 1000000000
DATA_SET = str(T_y_mid)+"-"+str(T_now)

REDIRECT_URI = 'http://127.0.0.1:3210/oauth2callback'

@app.route("/",methods=["GET"])
def auth1():
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
	authorize_url = flow.step1_get_authorize_url()
	webbrowser.open_new(authorize_url)
	#return "This is Only The user"
@app.route("/oauth2callback",methods=["GET"])
def assign():
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
	c = flask.request.args.get("code")
	print("This is the code which we get from thr server    ",c)
	code=c.strip()
	credentials = flow.step2_exchange(code)
	http = httplib2.Http()
	http = credentials.authorize(http)
	fitness_service = build('fitness', 'v1', http=http)
	weightData=fetchData("derived:com.google.weight:com.google.android.gms:merge_weight",fitness_service)
	saveSpeed(weightData,'Weight')
	saveData(weightData,'weight.txt')
	calories=fetchData('derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',fitness_service)
	saveSpeed(calories,'Calories')
	saveData(calories,'calories.txt')
	dist=fetchData('derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta',fitness_service)
	saveSpeed(dist,'Distance')
	saveData(dist,'distance.txt')
	heightData=fetchData("derived:com.google.height:com.google.android.gms:merge_height",fitness_service)
	saveSpeed(heightData,'Heart')
	saveData(heightData,'height.txt')
	heartData=fetchData('derived:com.google.heart_minutes:com.google.android.gms:merge_heart_minutes',fitness_service)
	saveSpeed(heartData,'Heart')
	saveData(heartData,'heart.txt')
	activityData=fetchData("derived:com.google.activity.segment:com.google.android.gms:merge_activity_segments",fitness_service)
	saveActivity(activityData,'Activity')
	saveData(activityData,'activity.txt')
	steps=fetchData(DATA_SOURCE,fitness_service)
	saveActivity(steps,'Steps')
	stps="Data Cleared..."
	return (stps)
def nanoseconds(nanotime):
    dt = datetime.fromtimestamp(nanotime // 1000000000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def saveData(data,path):
	with open('./data/'+path, 'w') as inputfile:
		json.dump(data, inputfile)
	pass
def fetchData(dataStreamId,fitness_service):
	dist=fitness_service.users().dataSources().datasets().get(userId='me', dataSourceId=dataStreamId, datasetId=DATA_SET).execute()
	return dist

def saveActivity(activityData,path):
	S_time,E_time,Type=[],[],[]
	stps={}
	for i in range(len(activityData["point"])):
		last_point = activityData["point"][i]
		S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
		E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
		Type.append(last_point["value"][0].get("intVal", None))
		stps.update({last_point["value"][0].get("intVal", None):[nanoseconds(int(last_point.get("startTimeNanos", 0))),nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
	adf = pd.DataFrame({'Start Time':S_time,'End Time':E_time,path:Type})
	adf.to_csv('./data/'+path+' '+Sdate+'.csv', columns=['Start Time','End Time',path], header=True,index = False)
	with open('./data/json/'+path+" "+Sdate+'.json', 'w') as outfile:
		json.dump(stps,outfile)

def saveSpeed(speedData,path):
  S_time,E_time,Speed=[],[],[]
  stps={}
  for i in range(len(speedData["point"])):
    last_point = speedData["point"][i]
    S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
    E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
    Speed.append(last_point["value"][0].get("fpVal", None))
    stps.update({last_point["value"][0].get("fpVal", None):[nanoseconds(int(last_point.get("startTimeNanos", 0))),nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
  #print(S_time)
  adf = pd.DataFrame({'Start Time':S_time,'End Time':E_time,path:Speed})
  #print(heartdf.head())
  adf.to_csv('./data/'+path+' '+Sdate+'.csv', columns=['Start Time','End Time',path], header=True,index = False)
  with open('./data/json/'+path+" "+Sdate+'.json', 'w') as outfile:
  	json.dump(stps,outfile)

if __name__ == "__main__":
	app.debug=True
	app.run(port=3210)
	print("Starting API services")

