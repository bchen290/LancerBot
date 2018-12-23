import datetime
import json
import os
import urllib
import urllib.request

import discord
from dateutil import parser
from discord import Embed
from discord.ext import commands


# noinspection PyMethodMayBeStatic
class CalendarCog:
    def __init__(self, bot):
        self.bot = bot

        api_key = os.getenv('calendar_api')

        if not api_key:
            with open('../calendar_api.txt', 'r') as file:
                api_key = file.readline()

        self.base_url = 'https://www.googleapis.com/calendar/v3/calendars/robolancers%40gmail.com/events?key=' + api_key + '&timeMin='

    def extract_time(self, data):
        if 'start' in data:
            if 'date' in data['start']:
                return (parser.parse(data['start']['date']) - datetime.datetime(1970, 1, 1)).total_seconds()
            elif 'dateTime' in data['start']:
                return (parser.parse(data['start']['dateTime']).replace(tzinfo=None) - datetime.datetime(1970, 1,
                                                                                                         1)).total_seconds()
            else:
                return 0
        else:
            return 0

    def filter_work_times(self, data):
        if 'summary' in data:
            if data['summary'] == 'FRC Work Time' or data['summary'] == 'RoboLancers Work Time':
                return False
            return True
        return False

    @commands.command(pass_context=True, name='event')
    async def _event(self, ctx, *, query):
        d = datetime.datetime.utcnow()
        url = self.base_url + d.isoformat('T') + 'Z'
        url += '&q=' + urllib.request.quote(query)

        contents = urllib.request.urlopen(url).read()
        parsed_json = json.loads(contents.decode())
        events = parsed_json['items']

        if not events:
            embed = Embed(title='No events found!', color=discord.Color.red())
            await ctx.channel.send(embed=embed)
            return

        team_embed = Embed(title='Events coming up!', color=discord.Color.green())

        events.sort(key=self.extract_time)
        events = list(filter(self.filter_work_times, events))

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

    @commands.command(pass_context=True, name='events')
    async def _events(self, ctx, *, month_name=None):
        d = datetime.datetime.utcnow()
        url = self.base_url + d.isoformat('T') + 'Z'

        contents = urllib.request.urlopen(url).read()
        parsed_json = json.loads(contents.decode())
        events = parsed_json['items']

        team_embed = Embed(title='Events coming up!', color=discord.Color.green())

        events.sort(key=self.extract_time)
        events = list(filter(self.filter_work_times, events))

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
            await ctx.channel.send(embed=team_embed)
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
                                    team_embed.add_field(name=event['summary'],
                                                         value=str(d.month) + '/' + str(d.day) + '/' + str(d.year),
                                                         inline=False)

            await ctx.channel.send(embed=team_embed)


def setup(bot):
    bot.add_cog(CalendarCog(bot))
