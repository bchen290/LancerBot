import os

import discord
import tbapy
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Cog
from prettytable import PrettyTable


class ArgumentError(Exception):
    """
    Custom exception for incorrect number of arguments in command
    """
    pass


class TBACog(Cog):
    def __init__(self, bot):
        self.bot = bot

        # If we are in Heroku then TBAKEY will be defined
        tba_key = os.getenv('TBAKEY')

        if tba_key:
            self.tba = tbapy.TBA(tba_key)
        else:
            # If we are in development then open the key from file
            with open('../tba_key.txt', 'r') as file:
                tba_key = file.readline()

            self.tba = tbapy.TBA(tba_key)

        self.teams_table = PrettyTable()
        self.teams_table.field_names = ['Team Name']

        # Max length of discord message
        self.MAX_LENGTH = 1900

    @commands.command(pass_context=True, name='tba')
    async def _tba(self, ctx):
        """
        Shows status for TBA
        """
        status_embed = Embed(title='TBA Status', url='https://www.thebluealliance.com', color=discord.Color.blue()) \
            .add_field(name='Current Season', value=str(self.tba.status().current_season)) \
            .add_field(name='Is TBA Down', value=str(self.tba.status().is_datafeed_down)) \
            .set_thumbnail(url='https://frcdesigns.files.wordpress.com/2017/06/android_launcher_icon_blue_512.png')

        await ctx.channel.send(embed=status_embed)

    @commands.command(pass_context=True, name='team')
    async def _team(self, ctx, *, team_number=None):
        """
        Gets information for team from TBA
        """

        try:
            if team_number:
                _ = int(team_number)

                team_info = self.tba.team(team='frc' + team_number)
                team_awards = self.tba.team_awards(team='frc' + team_number)

                team_awards.sort(key=lambda x: x.year, reverse=True)

                team_embed = Embed(title='Information for ' + team_number + ' (' + team_info.nickname + ')',
                                   color=discord.Color.blue(),
                                   url='https://www.thebluealliance.com/team/' + team_number) \
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

    @commands.command(pass_context=True, name='teams')
    async def _teams(self, ctx, *, page_number=0):
        """
        Get a list of of valid teams, where page * 500 is the starting team number.
        """
        teams = self.tba.teams(page=page_number)

        for team in teams:
            row = [str(team.team_number if team.team_number is not None else '') + ' (' + (
                team.nickname if team.nickname is not None else '') + ')']
            self.teams_table.add_row(row)

        table = self.teams_table.get_string().split('\n')
        current = ''

        for team in table:
            if len(current) < self.MAX_LENGTH:
                current += team + '\n'
            else:
                await ctx.channel.send('`' + current + '`')
                current = team + '\n'

        await ctx.channel.send('`' + current + '`')

        self.teams_table.clear_rows()


def setup(bot):
    bot.add_cog(TBACog(bot))
