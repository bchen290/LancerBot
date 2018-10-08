import urllib.request
import json
import datetime
from dateutil import parser
from pprint import pprint

API_KEY = 'AIzaSyBJNF9DXv3jVyqFEM0sYiLYPTv9vW-VFuE'
BASE_URL = 'https://www.googleapis.com/calendar/v3/calendars/robolancers%40gmail.com/events?key=' + API_KEY + '&timeMin='

d = datetime.datetime.utcnow()
URL = BASE_URL + d.isoformat('T') + 'Z'
print(URL)

contents = urllib.request.urlopen(URL).read()
parsed_json = json.loads(contents.decode())
events = parsed_json['items']


def extract_time(json):
    if 'start' in json:
        if 'date' in json['start']:
            return (parser.parse(json['start']['date']) - datetime.datetime(1970, 1, 1)).total_seconds()
        elif 'dateTime' in json['start']:
            return (parser.parse(json['start']['dateTime']).replace(tzinfo=None) - datetime.datetime(1970, 1, 1)).total_seconds()
        else:
            return 0
    else:
        return 0


def filter_work_times(json):
    if 'summary' in json:
        if json['summary'] == 'FRC Work Time' or json['summary'] == 'RoboLancers Work Time':
            return False
        return True
    return False


events.sort(key=extract_time)
events = list(filter(filter_work_times, events))

for event in events:
    if 'status' in event:
        if event['status'] != 'cancelled':
            if 'summary' in event:
                if 'start' in event:
                    start = event['start']

                    if 'date' in start:
                        date = start['date']
                        d = parser.parse(date)
                    elif 'dateTime' in start:
                        date_time = start['dateTime']
                        d = parser.parse(date_time)

                    current = datetime.datetime.utcnow()

                    if d.replace(tzinfo=None) > current.replace(tzinfo=None):
                        print(event['summary'])
                        print(d)
