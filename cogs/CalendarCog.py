import datetime
import json
import os
import urllib
import urllib.request

import discord
from dateutil import parser
from discord import Embed
from discord.ext import commands


# noinspection PyMethodMayBeStatic,PyUnusedLocal
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
                return (parser.parse(data['start']['dateTime']).replace(tzinfo=None) - datetime.datetime(1970, 1, 1)).total_seconds()
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

    def create_embed_from_events(self, events, date_embed, month):
        for event in events:
            try:
                if event['status'] != 'cancelled':
                    start = event['start']

                    time_of_event = datetime.datetime.utcnow()

                    if 'date' in start:
                        date = start['date']
                        time_of_event = parser.parse(date)
                    elif 'dateTime' in start:
                        date_time = start['dateTime']
                        time_of_event = parser.parse(date_time)

                    current = datetime.datetime.utcnow()

                    if month > 0:
                        if month == time_of_event.month:
                            date_embed.add_field(name=event['summary'],
                                                 value=str(time_of_event.month) + '/' + str(time_of_event.day) + '/' + str(time_of_event.year),
                                                 inline=False)
                    else:
                        date_embed.add_field(name=event['summary'],
                                             value=str(time_of_event.month) + '/' + str(time_of_event.day) + '/' + str(
                                                 time_of_event.year),
                                             inline=False)
            except KeyError:
                continue

    def get_data(self):
        url = self.base_url + datetime.datetime.utcnow().isoformat('T') + 'Z'

        contents = urllib.request.urlopen(url).read()
        parsed_json = json.loads(contents.decode())
        events = parsed_json['items']

        events.sort(key=self.extract_time)
        events = list(filter(self.filter_work_times, events))

        return events

    @commands.command(pass_context=True, aliases=['e', 'event', 'events'])
    async def _events(self, ctx, *, query=None):
        events = self.get_data()

        if not events:
            await ctx.channel.send(embed=Embed(title='No events found!', color=discord.Color.red()))
            return

        month = 0

        if query is not None:
            if query.isdigit():
                month = int(query)
            else:
                try:
                    month = datetime.datetime.strptime(query, '%B').month
                except ValueError:
                    query = query.lower()
                    events = [event for event in events if query in event['summary'].lower()]

        date_embed = Embed(title='Events coming up!', color=discord.Color.green())

        self.create_embed_from_events(events, date_embed, month)

        if not date_embed.fields:
            date_embed = Embed(title='No events found!', color=discord.Color.red())

        await ctx.channel.send(embed=date_embed)


def setup(bot):
    bot.add_cog(CalendarCog(bot))
