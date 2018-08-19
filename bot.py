import os
import discord
import asyncio
import numpy as np
import gspread

from prettytable import PrettyTable
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

bot = commands.Bot(command_prefix='>')

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


@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))


@bot.command(pass_context=True)
async def attendance(ctx, *, name=None):
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
            if idx == 0 or idx == 1 or idx == 2:
                pass
            else:
                fname, _, _ = value

                if fname == first_name:
                    results.append(value)

        if last_name is not None:
            for result in results:
                _, lname, _ = result

                if lname != last_name:
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
            await ctx.channel.send('`Error 404: ' + first_name + ' ' + (last_name if last_name is not None else ' ') +  'not found`')

        table.clear_rows()

    else:
        for idx, value in enumerate(zip(first_names, last_names, percentages)):
            if idx == 0 or idx == 1 or idx == 2:
                pass
            else:
                first_name, last_name, percentage = value
                row = [first_name, last_name, percentage,
                       '( ͡° ͜ʖ ͡°)' if float(percentage.strip('%')) >= 75 else '\(!!˚☐˚)/']
                table.add_row(row)

        await ctx.channel.send('`' + table.get_string(title='Attendance') + '`')
        await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

        table.clear_rows()

token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)
