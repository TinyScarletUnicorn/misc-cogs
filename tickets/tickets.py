import asyncio
import datetime
import logging
from contextlib import suppress
from io import BytesIO
from typing import Optional, NoReturn

import discord
from discord import app_commands
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from tsutils.helper_functions import repeating_timer

logger = logging.getLogger('red.misc-cogs.tickets')

class TicketType:
    REGULAR = 'regular'
    QUARANTINE = 'quarantine'
    REPORT = 'report'


class Tickets(commands.Cog):
    """write something here"""

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: Red = bot

        self.config = Config.get_conf(self, identifier=hash("tsubaki"))
        self.config.register_guild(
            alert_channel_id=None,
            alert_role_id=None,
            ticket_thread_channel_id=None,
            quarantine_role_id=None,  # Replace this with multi-command eventually
            threads={})

        self._loop = bot.loop.create_task(self.do_loop())

    def cog_unload(self):
        self._loop.cancel()

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data.

        No personal data is stored in this cog.
        """
        return

    async def do_loop(self) -> NoReturn:
        await self.bot.wait_until_ready()
        with suppress(asyncio.CancelledError):
            async for _ in repeating_timer(10 * 60):
                try:
                    await self.check_threads()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Error in loop:")

    async def check_threads(self):
        for gid, gd in (await self.config.all_guilds()).items():
            if (guild := self.bot.get_guild(gid)) is None:
                continue
            for tid, td in gd['threads'].items():
                thread = guild.get_thread(int(tid))
                if thread is not None and td['type'] == TicketType.REPORT and td['open'] == True:
                    time_diff = datetime.datetime.now(datetime.UTC) - thread.last_message.created_at
                    if time_diff.total_seconds() > 24 * 60 * 60:
                        await self.close_ticket(guild, thread)

    @commands.hybrid_group(name="tickets")
    @app_commands.default_permissions()
    @app_commands.guild_only()
    async def tickets(self, ctx):
        """The suite for ticket commands"""

    @commands.hybrid_group(name="modtickets")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.default_permissions()
    @app_commands.guild_only()
    async def modtickets(self, ctx):
        """The suite for ticket commands"""

    @tickets.group(name="setup", with_app_command=False)
    @checks.admin_or_permissions(manage_guild=True)
    async def ticket_setup(self, ctx):
        """Config"""

    @ticket_setup.command()
    async def set_ticket_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where tickets are created"""
        await self.config.guild(ctx.guild).ticket_thread_channel_id.set(channel.id)
        await confirm_command(ctx)

    @ticket_setup.command()
    async def set_alert_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where mods are notified"""
        await self.config.guild(ctx.guild).alert_channel_id.set(channel.id)
        await confirm_command(ctx)

    @ticket_setup.command()
    async def set_alert_role(self, ctx, role: discord.Role):
        """Set the mod role to ping on alerts"""
        await self.config.guild(ctx.guild).alert_role_id.set(role.id)
        await confirm_command(ctx)

    @ticket_setup.command()
    async def set_quarantine_role(self, ctx, *, role: discord.Role):
        """Set the role to give on a quarantine"""
        await self.config.guild(ctx.guild).quarantine_role_id.set(role.id)
        await confirm_command(ctx)

    @modtickets.command()
    async def quarantine(self, ctx, member: discord.Member):
        """[MOD ONLY] Quarantine a user"""
        if not await self.is_enabled(ctx):
            return
        quarantine_role = ctx.guild.get_role(await self.config.guild(ctx.guild).quarantine_role_id())
        if quarantine_role is None:
            return await ctx.send("Quarantine role not set.", ephemeral=True)
        if await self.make_ticket(ctx, member, TicketType.QUARANTINE) is not None:
            await confirm_command(ctx)

    @modtickets.command()
    async def sidechat(self, ctx, member: discord.Member):
        """[MOD ONLY] Create an open ticket with a member"""
        if not await self.is_enabled(ctx):
            return
        if await self.make_ticket(ctx, member, TicketType.REGULAR) is not None:
            await confirm_command(ctx)

    @tickets.command()
    async def report(self, ctx):
        """Create report ticket to speak with moderation"""
        if not await self.is_enabled(ctx):
            return

        if await self.make_ticket(ctx, ctx.author, TicketType.REPORT) is not None:
            await confirm_command(ctx)

    async def make_ticket(self, ctx, member: discord.Member, ticket_type: str) -> Optional[discord.Thread]:
        if not await self.is_enabled(ctx):
            return None
        base_channel = self.bot.get_channel(await self.config.guild(member.guild).ticket_thread_channel_id())
        await base_channel.set_permissions(member, view_channel=True)
        thread = await base_channel.create_thread(name=f"{member.name} - {datetime.datetime.now().strftime('%m/%d/%Y')}"
                                                       f" {'Q' if ticket_type == TicketType.QUARANTINE else 'R'}")
        await thread.send(member.mention + "\n" + self.type_to_message(ticket_type))
        await self.setup_ticket(ctx, thread, member, ticket_type)
        alert_role = ctx.guild.get_role(await self.config.guild(ctx.guild).alert_role_id())
        alert_channel = ctx.guild.get_channel(await self.config.guild(member.guild).alert_channel_id())
        await alert_channel.send(f"{alert_role.mention} A {ticket_type} ticket for {member.mention} has been"
                                 f" opened: {thread.jump_url}", allowed_mentions=discord.AllowedMentions.all())
        return thread

    async def setup_ticket(self, ctx, thread: discord.Thread, member: discord.Member, ticket_type: str):
        base_channel = self.bot.get_channel(await self.config.guild(member.guild).ticket_thread_channel_id())
        await base_channel.set_permissions(member, view_channel=True)
        async with self.config.guild(member.guild).threads() as threads:
            threads[str(thread.id)] = {
                "member": member.id,
                "type": ticket_type,
                "open": True
            }
        if ticket_type == TicketType.QUARANTINE:
            quarantine_role = ctx.guild.get_role(await self.config.guild(ctx.guild).quarantine_role_id())
            await member.add_roles(quarantine_role)

    @tickets.command()
    async def close(self, ctx, thread: Optional[discord.Thread], message: Optional[str]):
        """Close a ticket"""
        if thread is None:
            thread = ctx.guild.get_thread(ctx.channel.id)
        thread_dict = (await self.config.guild(ctx.guild).threads()).get(str(thread.id))
        if thread_dict is None:
            return await ctx.send("You must use this command within a ticket.", ephemeral=True)
        if ctx.author.id == thread_dict['member'] and thread_dict['type'] == TicketType.QUARANTINE:
            return await ctx.send("Only moderators may close quarantine tickets.", ephemeral=True)
        await self.close_ticket(ctx.guild, thread)
        if message:
            member = ctx.guild.get_member(thread_dict['member'])
            await member.send(message)
        return await confirm_command(ctx)

    async def close_ticket(self, guild: discord.Guild, thread: discord.Thread):
        async with self.config.guild(guild).threads() as threads:
            thread_dict = threads.get(str(thread.id))  # It serializes keys to strings
            thread_dict['open'] = False
            has_any_open_tickets = any(t['member'] == thread_dict['member'] and t['open'] for t in threads.values())

        member = guild.get_member(thread_dict['member'])
        await thread.remove_user(member)
        if not has_any_open_tickets:
            base_channel = self.bot.get_channel(await self.config.guild(member.guild).ticket_thread_channel_id())
            await base_channel.set_permissions(member, view_channel=None)

        # Ticket type handling
        if thread_dict['type'] == TicketType.QUARANTINE:
            quarantine_role = guild.get_role(await self.config.guild(guild).quarantine_role_id())
            if quarantine_role is not None:
                await member.remove_roles(quarantine_role)

    @modtickets.command()
    async def reopen(self, ctx, thread: Optional[discord.Thread]):
        """Re-open a ticket"""
        if thread is None:
            thread = ctx.guild.get_thread(ctx.channel.id)
        thread_dict = (await self.config.guild(ctx.guild).threads()).get(str(thread.id))
        if thread_dict is None:
            return await ctx.send("You must use this command within a ticket.", ephemeral=True)
        member = ctx.guild.get_member(thread_dict['member'])
        await self.setup_ticket(ctx, thread, member, thread_dict['type'])
        await thread.add_user(member)
        return await confirm_command(ctx)

    async def is_enabled(self, ctx) -> bool:
        if ctx.guild.get_channel(await self.config.guild(ctx.guild).alert_channel_id()) is None:
            await ctx.send("Alert channel not configured", ephemeral=True)
            return False
        if ctx.guild.get_role(await self.config.guild(ctx.guild).alert_role_id()) is None:
            await ctx.send("Alert role not configured", ephemeral=True)
            return False
        if ctx.guild.get_channel(await self.config.guild(ctx.guild).ticket_thread_channel_id()) is None:
            await ctx.send("Ticket thread channel not configured", ephemeral=True)
            return False
        return True

    @staticmethod
    def type_to_message(ticket_type: str) -> str:
        return {
            TicketType.REPORT: ("Thank you for opening a ticket. Please share your concerns and a"
                                " response will be received shortly. This ticket will be closed"
                                " after 24 hours of inactivity."),
            TicketType.QUARANTINE: ("You have been temporarily quarantined for breaking server rules."
                                    " Moderation will be with you shortly."),
            TicketType.REGULAR: "Server moderation has started a private conversation with you in this thread."
        }[ticket_type]


# TODO: Move to Tsutils
async def confirm_command(ctx: commands.Context):
    if ctx.interaction is None:
        await ctx.tick()
    else:
        await ctx.send("Done.", ephemeral=True)