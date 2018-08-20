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

bot = commands.Bot(command_prefix='>')


tba_key = os.getenv('TBAKEY')

if tba_key:
    tba = tbapy.TBA(tba_key)
else:
    with open('tba_key.txt', 'r') as file:
        tba_key = file.readline()

    tba = tbapy.TBA(tba_key)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credential_json = os.getenv('LancerAttendanceSheet.json')

if credential_json:
    with open('LancerAttendanceSheet.json', 'w+') as file:
        file.write(credential_json)
    credentials = ServiceAccountCredentials.from_json_keyfile_name('LancerAttendanceSheet.json', scope)
else:
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../LancerAttendanceSheet.json', scope)

gc = gspread.authorize(credentials)

worksheet = gc.open("LancerAttendance").sheet1

table = PrettyTable()
table.field_names = ['First Name', 'Last Name', 'Attendance %', 'Met Requirements']
table.align['First Name'] = 'l'
table.align['Last Name'] = 'l'
table.align['Attendance %'] = 'l'


class ArgumentError(Exception):
    pass


class ScheduleThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        schedule.every().day.at("00:01").do(self.send_all_attendance)

    async def send_all_attendance(self):
        gc.login()

        first_names = worksheet.col_values(1)
        last_names = worksheet.col_values(2)
        percentages = worksheet.col_values(4)

        for idx, value in enumerate(zip(first_names, last_names, percentages)):
            if is_useless_row(idx):
                pass
            else:
                first_name, last_name, percentage = value
                row = [first_name, last_name, percentage,
                       '( ͡° ͜ʖ ͡°)' if float(percentage.strip('%')) >= 75 else '\(!!˚☐˚)/']
                table.add_row(row)

        channel = bot.get_channel(480886868326481941)
        await channel.send('`' + table.get_string(title='Attendance') + '`')
        await channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

        table.clear_rows()

    def run(self):
        schedule.run_pending()
        time.sleep(1)


def is_useless_row(idx):
    if idx == 0 or idx == 1 or idx == 2 or idx == 3:
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

            row = [fname, lname, percentage,
                   '( ͡° ͜ʖ ͡°)' if float(percentage.strip('%')) >= 75 else '\(!!˚☐˚)/']
            table.add_row(row)

        if len(results) > 0:
            await ctx.channel.send('`' + table.get_string(title='Attendance for ' + first_name) + '`')
            await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')
        else:
            await ctx.channel.send('`Error 404: ' + first_name + ' ' + (last_name + ' ' if last_name is not None else '') +  'not found`')

        table.clear_rows()

    else:
        for idx, value in enumerate(zip(first_names, last_names, percentages)):
            if is_useless_row(idx):
                pass
            else:
                first_name, last_name, percentage = value
                row = [first_name, last_name, percentage,
                       '( ͡° ͜ʖ ͡°)' if float(percentage.strip('%')) >= 75 else '\(!!˚☐˚)/']
                table.add_row(row)

        attendance_table = table.get_string().split('\n')
        current = ''

        for attendance in attendance_table:
            if len(current) < 1900:
                current += attendance + '\n'
            else:
                await ctx.channel.send('`' + current + '`')
                current = attendance + '\n'

        await ctx.channel.send('`' + current + '`')
        await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

        table.clear_rows()


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

            team_info = tba.team('frc' + team_number)

            team_embed = Embed(title='Information for ' + team_number + ' (' + team_info.nickname + ')',
                               color=discord.Color.blue(), url='https://www.thebluealliance.com/team/' + team_number) \
                .add_field(name='Team Location', value=team_info.city + ', ' + team_info.country) \
                .add_field(name='Team Website', value=team_info.website)

            await ctx.channel.send(embed=team_embed)
        else:
            raise ArgumentError

    except (ValueError, ArgumentError):
        error_embed = Embed(title='Error(Bad Usage)', color=discord.Color.red()) \
            .add_field(name='Usage', value='>team [teamNumber]')

        await ctx.channel.send(embed=error_embed)

    except AttributeError:
        error_embed = Embed(color=discord.Color.red()) \
            .add_field(name='Error', value='Team Not Found')

        await ctx.channel.send(embed=error_embed)


@bot.command(pass_context=True, name='teams')
async def _teams(ctx, *, page=1):
    """
    Get a list of of valid teams, where page * 500 is the starting team number.
    """
    print(tba.teams(page=page))
    await ctx.channel.send(" ")


token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)

thread = ScheduleThread()
thread.start()
