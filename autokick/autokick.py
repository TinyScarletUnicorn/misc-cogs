import logging
from io import BytesIO

import discord
from redbot.core import Config, checks, commands

logger = logging.getLogger('red.misc-cogs.autokick')


class AutoKick(commands.Cog):
    """Autokick members on certain conditions"""

    DM_TEXT = ("Your account has displayed anomolous behavior in our server indicative of"
               " botting, and we're kicking you. If you are human and believe this to be in"
               " error, please rejoin & contact mods.")

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.config = Config.get_conf(self, identifier=3260)
        self.config.register_guild(kick_role=None, log_channel=None)

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    @commands.group()
    @checks.mod()
    async def autokick(self, ctx):
        """Autokick users"""

    @autokick.group(name='role')
    async def ak_role(self, ctx):
        """Autokick users by role"""

    @ak_role.command(name="set")
    async def ak_r_set(self, ctx, role: discord.Role):
        """Set the autokick role"""
        await self.config.guild(ctx.guild).kick_role.set(role.id)
        await ctx.tick()

    @ak_role.command(name="optout")
    async def ak_r_optout(self, ctx):
        """Remove the autokick role"""
        await self.config.guild(ctx.guild).kick_role.set(None)
        await ctx.tick()

    @autokick.group(name='channel')
    async def ak_channel(self, ctx):
        """Autokick logging channel"""

    @ak_channel.command(name="set")
    async def ak_c_set(self, ctx, channel: discord.TextChannel):
        """Set the autokick log channel"""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.tick()

    @ak_channel.command(name="remove")
    async def ak_c_optout(self, ctx):
        """Remove the autokick log channel"""
        await self.config.guild(ctx.guild).log_channel.set(None)
        await ctx.tick()

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, _, member):
        if (kr_id := await self.config.guild(member.guild).kick_role()) is None:
            return
        if not (kick_role := member.guild.get_role(kr_id)):
            return
        if kick_role in member.roles:
            try:
                await member.send(self.DM_TEXT)
            except discord.Forbidden:
                pass
            try:
                await member.kick(reason='AutoKick Role')
                await self.log_kick(member)
            except discord.Forbidden:
                logger.exception(f"Unable to kick user {member}")

    async def log_kick(self, member: discord.Member):
        if (ch_id := await self.config.guild(member.guild).log_channel()) is None:
            return
        if (ch := member.guild.get_channel(ch_id)) is None:
            return
        await ch.send(f"{member.name} was kicked by AutoKick for adding a honeypot role.")

    async def kick_users(self):
        for gid in await self.config.all_guilds():
            if not (guild := self.bot.get_guild(gid)):
                continue
            if (kr_id := await self.config.guild(guild).kick_role()) is None:
                continue
            if not (kick_role := guild.get_role(kr_id)):
                continue
            for baduser in kick_role.members:
                try:
                    await baduser.send(self.DM_TEXT)
                except discord.Forbidden:
                    pass
                try:
                    await baduser.kick(reason='AutoKick Role')
                    await self.log_kick(baduser)
                except discord.Forbidden:
                    logger.exception(f"Unable to kick user {baduser}")
