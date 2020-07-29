import os

from fa_search_bot.bot import FASearchBot

bot = FASearchBot(os.getenv('CONFIG_FILE', 'config.json'))
bot.start()
