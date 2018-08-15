import os

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='`')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def greet(ctx):
    await ctx.send(":smiley: :wave: Hello, there!")


try:
    bot.run(os.environ['TOKEN'])
except KeyError:
    with open('bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)
