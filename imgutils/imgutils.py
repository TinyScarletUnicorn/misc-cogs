import logging
from io import BytesIO

import discord
from PIL import Image
from redbot.core import commands
from redbot.core.bot import Red

logger = logging.getLogger('red.misc-cogs.imgutils')


class ImgUtils(commands.Cog):
    """Do stuff with images."""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    @commands.command()
    async def swatch(self, ctx, *, color):
        if not (color.startswith('0x') or color.startswith('rgb')):
            color = '0x' + color
        try:
            color = discord.Color.from_str(color).to_rgb()
        except ValueError:
            await ctx.send("Invalid input. Please provide a hex code of the color you want.")
            return

        fio = BytesIO()
        Image.new("RGB", (100, 100), color).save(fio, format='PNG')
        fio.seek(0)
        await ctx.send(file=discord.File(fio, 'swatch.png'))
