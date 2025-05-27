from discord.ext import commands
from .tournament import Tournament
from .Config import BotConfig

class TOBot(commands.Bot):
    def __init__(self, config: BotConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.tournaments: dict[int, Tournament] = {}