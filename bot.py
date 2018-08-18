import os
import discord
import asyncio
import numpy as np
import gspread

from prettytable import PrettyTable
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

bot = commands.Bot('`')

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
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('`attendance'):
        gc.login()
        first_names = worksheet.col_values(1)
        last_names = worksheet.col_values(2)
        percentages = worksheet.col_values(4)

        for i in range(len(first_names)):

            if i == 0 or i == 1 or i == 2:
                pass
            else:
                if float(percentages[i][:-1]) > 75:
                    row = [first_names[i], last_names[i], percentages[i], '( ͡° ͜ʖ ͡°)']
                else:
                    row = [first_names[i], last_names[i], percentages[i], '\(!!˚☐˚)/']

                table.add_row(row)

        await bot.send_message(message.channel, '`' + table.get_string(title='Attendance') + '`')
        await bot.send_message(message.channel, '`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')
    elif message.content.startswith('`test'):
        await bot.send_message(message.channel, '```css\ntesting 1 2 3\n```')


token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)
