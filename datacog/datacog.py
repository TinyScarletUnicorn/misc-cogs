import logging
from io import BytesIO

from redbot.core import Config, commands
from redbot.core.bot import Red

logger = logging.getLogger('red.misc-cogs.datacog')


class DataCog(commands.Cog):
    """Get bot data."""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.config = Config.get_conf(self, identifier=3260)
        self.config.register_global(usages={}, lastreset=0)

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    @commands.Cog.listener('on_message')
    async def mod_message(self, message):
        content = message.content
        for prefix in await self.bot.get_valid_prefixes():
            if content.startswith(prefix):
                content = content[len(prefix):]
                break
        else:
            return

        command = content.split()[0]

        async with self.config.usages() as usages:
            usages.setdefault(command, 0)
            usages[command] += 1
