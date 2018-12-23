import os

import gspread
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from prettytable import PrettyTable


class AttendanceCog:
    def __init__(self, bot):
        self.bot = bot

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

        self.gc = gspread.authorize(credentials)

        self.FRC_attendance_worksheet = self.gc.open("LancerAttendance").sheet1
        self.FTC_attendance_worksheet = self.gc.open("LancerAttendance").worksheet("FTC")

        # Setting up pretty table and styling it
        self.attendance_table = PrettyTable()
        self.attendance_table.field_names = ['First Name', 'Last Name', 'Attendance %', 'Met Requirements']
        self.attendance_table.align['First Name'] = 'l'
        self.attendance_table.align['Last Name'] = 'l'
        self.attendance_table.align['Attendance %'] = 'l'

        # Start index for the rows of the attendance sheet
        self.START_INDEX = 3

        # Max length of discord message
        self.MAX_LENGTH = 1900

    @commands.command(pass_context=True, name='frc')
    async def _attendance_frc(self, ctx, *, param=None):
        await self.display_attendance(ctx, is_frc=True, param=param)

    @commands.command(pass_context=True, name='ftc')
    async def _attendance_ftc(self, ctx, *, param=None):
        await self.display_attendance(ctx, is_frc=False, param=param)

    async def display_attendance(self, ctx, is_frc, param=None):
        """
        If param is specified, allows people to sort by ascending/descending (up/down) order
        Also allows people to search their own name
        """
        self.gc.login()

        if is_frc:
            first_names = self.FRC_attendance_worksheet.col_values(1)
            last_names = self.FRC_attendance_worksheet.col_values(2)
            percentages = self.FRC_attendance_worksheet.col_values(5)
        else:
            first_names = self.FTC_attendance_worksheet.col_values(1)
            last_names = self.FTC_attendance_worksheet.col_values(2)
            percentages = self.FTC_attendance_worksheet.col_values(4)

        first_names = first_names[self.START_INDEX:]
        last_names = last_names[self.START_INDEX:]
        percentages = percentages[self.START_INDEX:]

        percentages = [float(percent.replace('%', '')) for percent in percentages]

        attendance_list = [attendance for attendance in zip(first_names, last_names, percentages)]

        if param:
            params = param.lower().split(' ')
            # Allows people to sort the table with ascending or descending values
            if params[0] == 'up' or params[0] == 'down':
                is_descending = params[0] == 'down'
                choices = {'first': 0, 'last': 1, 'percent': 2}

                try:
                    column = params[1]
                except IndexError:
                    column = 0

                attendance_list = sorted(attendance_list, key=lambda x: x[choices.get(column, 0)],
                                         reverse=is_descending)

            # Allows people to input a name to check attendance
            else:
                first_name = params[0]

                try:
                    last_name = params[1]
                except IndexError:
                    last_name = ''

                attendance_list = [name for name in attendance_list if
                                   name[0].lower().find(first_name) != -1 and name[1].lower().find(last_name) != -1]

                if len(attendance_list) > 0:
                    self.attendance_table.title = 'Attendance for ' + attendance_list[0][0]
                else:
                    await ctx.channel.send('`Error 404: ' + first_name + ' ' + last_name + ' not found`')
                    return

        for value in attendance_list:
            first_name, last_name, percent = value

            if percent > 100:
                emoji = '( ▀ ͜͞ʖ▀)'
            elif 75 <= percent <= 100:
                emoji = '( ͡° ͜ʖ ͡°)'
            else:
                emoji = '\(!!˚☐˚)/'

            row = [first_name, last_name, str(percent) + '%', emoji]

            self.attendance_table.add_row(row)

        table = self.attendance_table.get_string().split('\n')
        current = ''

        for attendance in table:
            if len(current) < self.MAX_LENGTH:
                current += attendance + '\n'
            else:
                await ctx.channel.send('`' + current + '`')
                current = attendance + '\n'

        await ctx.channel.send('`' + current + '`')
        await ctx.channel.send('`' + '\(!!˚☐˚)/ = Not meeting 75% requirement' + '`')

        self.attendance_table.clear_rows()


def setup(bot):
    bot.add_cog(AttendanceCog(bot))
