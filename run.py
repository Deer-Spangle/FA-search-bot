import os

from bot import FASearchBot

bot = FASearchBot(os.getenv('CONFIG_FILE', 'config.json'))
bot.start()
