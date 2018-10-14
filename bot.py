import datetime
import numbers
import os
import threading

import schedule
import time
import gspread
import tbapy
import discord

from prettytable import PrettyTable
from discord.ext import commands
from discord.embeds import Embed
from oauth2client.service_account import ServiceAccountCredentials

import urllib
import urllib.request
import json
import datetime
from dateutil import parser
import calendar

bot = commands.Bot(command_prefix='>')

# If we are in Heroku then TBAKEY will be defined
tba_key = os.getenv('TBAKEY')

if tba_key:
    tba = tbapy.TBA(tba_key)
else:
    # If we are in development then open the key from file
    with open('tba_key.txt', 'r') as file:
        tba_key = file.readline()

    tba = tbapy.TBA(tba_key)

# Setting up Google API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Again checking if we are using Heroku
credential_json = os.getenv('LancerAttendanceSheet.json')

if credential_json:
    # We do not want to upload the json file we will grab it from environment and create a file for google to use
    with open('LancerAttendanceSheet.json', 'w+') as file:
        file.write(credential_json)
    credentials = ServiceAccountCredentials.from_json_keyfile_name('LancerAttendanceSheet.json', scope)
else:
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../LancerAttendanceSheet.json', scope)

gc = gspread.authorize(credentials)

worksheet = gc.open("LancerAttendance").sheet1

API_KEY = os.getenv('calendar_api')

if not API_KEY:
    with open('calendar_api.txt', 'r') as file:
        API_KEY = file.readline()

BASE_URL = 'https://www.googleapis.com/calendar/v3/calendars/robolancers%40gmail.com/events?key=' + API_KEY + '&timeMin='

# Setting up pretty table and styling it
attendance_table = PrettyTable()
attendance_table.field_names = ['First Name', 'Last Name', 'Attendance %', 'Met Requirements']
attendance_table.align['First Name'] = 'l'
attendance_table.align['Last Name'] = 'l'
attendance_table.align['Attendance %'] = 'l'

teams_table = PrettyTable()
teams_table.field_names = ['Team Name']


class ArgumentError(Exception):
    """
    Custom exception for incorrect number of arguments in command
    """
    pass


def is_useless_row(idx):
    """
    Checks if the current index is a useless index as specified in the sheets
    """
    if idx == 0 or idx == 1 or idx == 2:
        return True

    return False


@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))


@bot.command(pass_context=True, name='attendance')
async def _attendance(ctx, *, name=None):
    """
    If name is specified, shows attendance for people with that name else shows attendance for everyone
    Also works with just first names
    """
    gc.login()

    first_names = worksheet.col_values(1)
    last_names = worksheet.col_values(2)
    percentages = worksheet.col_values(4)

    if name:
        results = []

        split_name = name.split(' ')
        first_name = split_name[0]

        try:
            last_name = split_name[1]
        except IndexError:
            last_name = None

        for idx, value in enumerate(zip(first_names, last_names, percentages)):
            if is_useless_row(idx):
                pass
            else:
                fname, _, _ = value

                if fname.lower() == first_name.lower():
                    results.append(value)

        if last_name is not None:
            for result in results:
                _, lname, _ = result

                if lname.lower() != last_name.lower():
                    results.remove(result)

        for result in results:
            fname, lname, percentage = result

            percent = float(percentage.strip('%'))

            if percent > 100:
                row = [fname, lname, percentage, '( ▀ ͜͞ʖ▀)']
            elif 75 <= percent <= 100:
                row = [fname, lname, percentage, '( ͡° ͜ʖ ͡°)']
            else:
                row = [fname, lname, percentage, '\(!!˚☐˚)/']

            attendance_table.add_row(row)

        if len(results) > 0:
            await ctx.channel.send('`' + attendance_table.get_string(title='Attendance for ' + first_name) + '`')
            await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')
        else:
            await ctx.channel.send('`Error 404: ' + first_name + ' ' + (last_name + ' ' if last_name is not None else '') +  'not found`')

        attendance_table.clear_rows()

    else:
        for idx, value in enumerate(zip(first_names, last_names, percentages)):
            if is_useless_row(idx):
                pass
            else:
                first_name, last_name, percentage = value

                percent = float(percentage.strip('%'))

                if percent > 100:
                    row = [first_name, last_name, percentage, '( ▀ ͜͞ʖ▀)']
                elif 75 <= percent <= 100:
                    row = [first_name, last_name, percentage, '( ͡° ͜ʖ ͡°)']
                else:
                    row = [first_name, last_name, percentage, '\(!!˚☐˚)/']

                attendance_table.add_row(row)

        table = attendance_table.get_string().split('\n')
        current = ''

        for attendance in table:
            if len(current) < 1900:
                current += attendance + '\n'
            else:
                await ctx.channel.send('`' + current + '`')
                current = attendance + '\n'

        await ctx.channel.send('`' + current + '`')
        await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

        attendance_table.clear_rows()


@bot.command(pass_context=True, name='tba')
async def _tba(ctx):
    """
    Shows status for TBA
    """
    status_embed = Embed(title='TBA Status', url='https://www.thebluealliance.com', color=discord.Color.blue())\
        .add_field(name='Current Season', value=str(tba.status().current_season))\
        .add_field(name='Is TBA Down', value=str(tba.status().is_datafeed_down))\
        .set_thumbnail(url='https://frcdesigns.files.wordpress.com/2017/06/android_launcher_icon_blue_512.png')

    await ctx.channel.send(embed=status_embed)


@bot.command(pass_context=True, name='team')
async def _team(ctx, *, team_number=None):
    """
    Gets information for team from TBA
    """

    try:
        if team_number:
            _ = int(team_number)

            team_info = tba.team(team='frc' + team_number)
            team_awards = tba.team_awards(team='frc' + team_number)

            team_awards.sort(key=lambda x: x.year, reverse=True)

            team_embed = Embed(title='Information for ' + team_number + ' (' + team_info.nickname + ')',
                               color=discord.Color.blue(), url='https://www.thebluealliance.com/team/' + team_number) \
                .add_field(name='Team Location', value=team_info.city + ', ' + team_info.country) \
                .add_field(name='Number of awards', value=len(team_awards))

            await ctx.channel.send(embed=team_embed)
        else:
            raise ArgumentError

    except (ValueError, ArgumentError) as e:
        print(e)
        error_embed = Embed(title='Error(Bad Usage or Team Not Found)', color=discord.Color.red()) \
            .add_field(name='Usage', value='>team [teamNumber]')

        await ctx.channel.send(embed=error_embed)

    except AttributeError:
        error_embed = Embed(color=discord.Color.red()) \
            .add_field(name='Error', value='Team Not Found')

        await ctx.channel.send(embed=error_embed)


@bot.command(pass_context=True, name='teams')
async def _teams(ctx, *, page_number=0):
    """
    Get a list of of valid teams, where page * 500 is the starting team number.
    """
    teams = tba.teams(page=page_number)

    for team in teams:
        row = [str(team.team_number if team.team_number is not None else '') + ' (' + (team.nickname if team.nickname is not None else '') + ')']
        teams_table.add_row(row)

    table = teams_table.get_string().split('\n')
    current = ''

    for team in table:
        if len(current) < 1900:
            current += team + '\n'
        else:
            await ctx.channel.send('`' + current + '`')
            current = team + '\n'

    await ctx.channel.send('`' + current + '`')

    teams_table.clear_rows()


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


@bot.command(pass_context=True, name='event')
async def _event(ctx, *, query):
    d = datetime.datetime.utcnow()
    URL = BASE_URL + d.isoformat('T') + 'Z'
    URL += '&q=' + urllib.request.quote(query)

    contents = urllib.request.urlopen(URL).read()
    parsed_json = json.loads(contents.decode())
    events = parsed_json['items']

    if not events:
        embed = Embed(title='No events found!', color=discord.Color.red())
        await ctx.channel.send(embed=embed)
        return

    team_embed = Embed(title='Events coming up!', color=discord.Color.green())

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
                            team_embed.add_field(name=event['summary'],
                                                 value=str(d.month) + '/' + str(d.day) + '/' + str(d.year),
                                                 inline=False)

    await ctx.channel.send(embed=team_embed)


@bot.command(pass_context=True, name='events')
async def _events(ctx, *, month_name=None):
    d = datetime.datetime.utcnow()
    URL = BASE_URL + d.isoformat('T') + 'Z'

    contents = urllib.request.urlopen(URL).read()
    parsed_json = json.loads(contents.decode())
    events = parsed_json['items']

    team_embed = Embed(title='Events coming up!', color=discord.Color.green())

    events.sort(key=extract_time)
    events = list(filter(filter_work_times, events))

    if month_name:
        try:
            month = int(month_name)
        except ValueError:
            month = datetime.datetime.strptime(month_name, '%B').month

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

                            if d.replace(tzinfo=None) >= current.replace(tzinfo=None):
                                if d.month == month:
                                    team_embed.add_field(name=event['summary'],
                                                         value=str(d.month) + '/' + str(d.day) + '/' + str(d.year),
                                                         inline=False)

    else:
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
                                team_embed.add_field(name=event['summary'], value=str(d.month) + '/' + str(d.day) + '/' + str(d.year), inline=False)

        await ctx.channel.send(embed=team_embed)


token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)
