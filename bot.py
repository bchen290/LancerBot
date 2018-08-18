import os
import discord
import asyncio
import numpy as np
import gspread

from prettytable import PrettyTable
import discord
from oauth2client.service_account import ServiceAccountCredentials

client = discord.Client()

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


@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
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
                if float(percentages[i][:-1]) >= 75:
                    row = [first_names[i], last_names[i], percentages[i], '( ͡° ͜ʖ ͡°)']
                else:
                    row = [first_names[i], last_names[i], percentages[i], '\(!!˚☐˚)/']

                table.add_row(row)

        await message.channel.send('`' + table.get_string(title='Attendance') + '`')
        await message.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

token = os.getenv('TOKEN')
if token:
    client.run(token)
else:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        client.run(token)
