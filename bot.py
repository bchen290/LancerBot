import os
from discord.ext import commands

bot = commands.Bot(command_prefix='>')

bot.load_extension('cogs.AttendanceCog')
bot.load_extension('cogs.TBACog')
bot.load_extension('cogs.CalendarCog')


@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    with open('../bot_token.txt') as bot_token_file:
        token = bot_token_file.readline()

        bot.run(token)
