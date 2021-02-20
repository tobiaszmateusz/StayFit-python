#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from turtle import pd
import pandas as pd
import httplib2
import flask
import webbrowser
import time
from datetime import datetime
from datetime import timedelta
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

app = flask.Flask(__name__)
# Copy your credentials from the Google Developers Console
CLIENT_ID = '318059335787-9f8ah6dm5d95iu967jm00lub3oadi4dj.apps.googleusercontent.com'
CLIENT_SECRET = '6NpRrtoSqExnkFFpGteC5Y0A'

# Check https://developers.google.com/fit/rest/v1/reference/users/dataSources/datasets/get
# for all available scopes
# OAUTH_SCOPE = 'https://www.googleapis.com/auth/fitness.activity.read'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/fitness.activity.read https://www.googleapis.com/auth/fitness.blood_glucose.read https://www.googleapis.com/auth/fitness.blood_pressure.read https://www.googleapis.com/auth/fitness.body_temperature.read https://www.googleapis.com/auth/fitness.location.read https://www.googleapis.com/auth/fitness.nutrition.read https://www.googleapis.com/auth/fitness.oxygen_saturation.read https://www.googleapis.com/auth/fitness.body.read https://www.googleapis.com/auth/fitness.reproductive_health.read'

# DATA SOURCE
DATA_SOURCE = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"

# The ID is formatted like: "startTime-endTime" where startTime and endTime are
# 64 bit integers (epoch time with nanoseconds).
TODAY = datetime.today().date()
NOW = datetime.today()
START = int(time.mktime(TODAY.timetuple()) * 1000000000)
END = int(time.mktime(NOW.timetuple()) * 1000000000)
DATA_SET = "%s-%s" % (START, END)

# Redirect URI for installed apps
REDIRECT_URI = 'http://127.0.0.1:3210/oauth2callback'


@app.route("/", methods=["GET"])
def auth1():
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
    authorize_url = flow.step1_get_authorize_url()
    webbrowser.open_new(authorize_url)
    return (print("okay"))


@app.route("/oauth2callback", methods=["GET"])
def assign():
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
    c = flask.request.args.get("code")
    print("This is the code which we get from thr server    ", c)
    code = c.strip()
    credentials = flow.step2_exchange(code)
    http = httplib2.Http()
    http = credentials.authorize(http)
    fitness_service = build('fitness', 'v1', http=http)
    steps = fetchData(DATA_SOURCE, fitness_service)
    saveActivity(steps, 'Steps')
    Show(steps)
    dist = fetchData('derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta', fitness_service)
    saveDist(dist, 'Distance')
    Show2(dist)
    stps = "Data Cleared..."
    return stps


def Show(dataset):
    starts = []
    ends = []
    values = []
    for point in dataset["point"]:
        if int(point["startTimeNanos"]) > START:
            starts.append(int(point["startTimeNanos"]))
            ends.append(int(point["endTimeNanos"]))
            values.append(point['value'][0]['intVal'])
    print("From: ", nanoseconds(min(starts)))
    print("To: ", nanoseconds(max(ends)))
    print("Steps: %d" % sum(values))


def Show2(dataset):
    starts = []
    ends = []
    values = []
    for point in dataset["point"]:
        if int(point["startTimeNanos"]) > START:
            starts.append(int(point["startTimeNanos"]))
            ends.append(int(point["endTimeNanos"]))
            values.append(point['value'][0]['fpVal'])
    print("From: ", nanoseconds(min(starts)))
    print("To: ", nanoseconds(max(ends)))
    print("Distance: %d" % sum(values))


def fetchData(dataStreamId, fitness_service):
    dist = fitness_service.users().dataSources().datasets().get(userId='me', dataSourceId=dataStreamId,
                                                                datasetId=DATA_SET).execute()
    return dist


def saveActivity(activityData, path):
    S_time, E_time, Type = [], [], []
    stps = {}
    for i in range(len(activityData["point"])):
        last_point = activityData["point"][i]
        S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
        E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
        Type.append(last_point["value"][0].get("intVal", None))
        stps.update({last_point["value"][0].get("intVal", None): [nanoseconds(int(last_point.get("startTimeNanos", 0))),
                                                                  nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
    # print(S_time)
    adf = pd.DataFrame({'Start Time': S_time, 'End Time': E_time, path: Type})
    # print(heartdf.head())
    adf.to_csv('./data/' + path + ' .csv', columns=['Start Time', 'End Time', path], header=True, index=False)
    with open('./data/json/' + path + ' .json', 'w') as outfile:
        json.dump(stps, outfile)


def saveDist(speedData, path):
    S_time, E_time, Speed = [], [], []
    stps = {}
    for i in range(len(speedData["point"])):
        last_point = speedData["point"][i]
        S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
        E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
        Speed.append(last_point["value"][0].get("fpVal", None))
        stps.update({last_point["value"][0].get("fpVal", None): [nanoseconds(int(last_point.get("startTimeNanos", 0))),
                                                                 nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
    # print(S_time)
    adf = pd.DataFrame({'Start Time': S_time, 'End Time': E_time, path: Speed})
    # print(heartdf.head())
    adf.to_csv('./data/' + path + ' .csv', columns=['Start Time', 'End Time', path], header=True, index=False)
    with open('./data/json/' + path + ' .json', 'w') as outfile:
        json.dump(stps, outfile)


def nanoseconds(nanotime):
    dt = datetime.fromtimestamp(nanotime // 1000000000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


if __name__ == "__main__":
    app.run(port=3210)
    # Point of entry in execution mode:
    auth1()
    dataset = assign()
    with open('dataset.txt', 'w') as outfile:
        json.dump(dataset, outfile)

    starts = []
    ends = []
    values = []
    for point in dataset["point"]:
        if int(point["startTimeNanos"]) > START:
            starts.append(int(point["startTimeNanos"]))
            ends.append(int(point["endTimeNanos"]))
            values.append(point['value'][0]['intVal'])
    print("From: ", nanoseconds(min(starts)))
    print("To: ", nanoseconds(max(ends)))
    print("Steps: %d" % sum(values))
