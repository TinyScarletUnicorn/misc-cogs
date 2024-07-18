from io import BytesIO

import discord
from redbot.core import Config, commands


class RoleTools(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2552)
        self.config.register_guild(badroles=[], stickyroles=[])
        self.config.register_member(stickyroles=[])

    async def red_get_data_for_user(self, *, user_id):
        """Get a user's personal data."""
        data = "No data is stored for user with ID {}.\n".format(user_id)
        return {"user_data.txt": BytesIO(data.encode())}

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Delete a user's personal data."""
        await self.config.user_from_id(user_id).clear()

    @commands.group()
    async def badrole(self, ctx):
        """The suite for badroles

        A badrole does not have access to any channel that it's not explicitly given,
        and will continue to update as new channels are created."""

    @badrole.command(name='add')
    async def br_add(self, ctx, role: discord.Role):
        """Add a badrole"""
        async with self.config.guild(ctx.guild).badroles() as brs:
            if role.id in brs:
                return await ctx.send("This role is already a badrole.")
            brs.append(role.id)

        for channel in ctx.guild.channels:
            await channel.set_permissions(role, read_messages=False)

        await ctx.tick()

    @badrole.command(name='remove')
    async def br_rm(self, ctx, role: discord.Role):
        """Remove a badrole"""
        async with self.config.guild(ctx.guild).badroles() as brs:
            if role.id not in brs:
                return await ctx.send("This role is not a badrole.")
            brs.remove(role.id)
        await ctx.tick()

    @badrole.command(name='list')
    async def br_list(self, ctx):
        """List badroles"""
        brs = await self.config.guild(ctx.guild).badroles()
        await ctx.send("\n".join(f'<@{r.id}>' for r in brs),
                       allowed_mentions=discord.AllowedMentions.none)

    @commands.Cog.listener('on_guild_channel_create')
    async def br_on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        brs = await self.config.guild(channel.guild).badroles()
        for br in brs:
            role = channel.guild.get_role(br)
            if role is None:
                continue
            await channel.set_permissions(role, read_messages=False)

    @commands.group()
    async def stickyrole(self, ctx):
        """The suite for sticky roles

        A sticky role remains if a user leaves and rejoins a server."""

    @stickyrole.command(name='add')
    async def sr_add(self, ctx, role: discord.Role):
        """Add a sticky role"""
        if not role.is_assignable():
            return await ctx.send("This role is not assignable. Please make sure my role is higher on the role heirarchy.")

        async with self.config.guild(ctx.guild).stickyroles() as srs:
            if role.id in srs:
                return await ctx.send("This role is already a sticky role.")
            srs.append(role.id)

        for member in ctx.guild.members:
            if role in member.roles:
                async with self.config.member(member).stickyroles() as srs:
                    srs.append(role.id)

        await ctx.tick()

    @stickyrole.command(name='remove')
    async def sr_rm(self, ctx, role: discord.Role):
        """Remove a sticky role"""
        async with self.config.guild(ctx.guild).stickyroles() as srs:
            if role.id not in srs:
                return await ctx.send("This role is not a sticky role.")
            srs.remove(role.id)

        for mid, data in (await self.config.all_members(ctx.guild)).items():
            if role.id in data['stickyroles']:
                async with self.config.member_from_ids(ctx.guild.id, mid).stickyroles() as srs:
                    srs.append(role.id)

        await ctx.tick()

    @stickyrole.command(name='list')
    async def sr_list(self, ctx):
        """List sticky roles"""
        srs = await self.config.guild(ctx.guild).stickyroles()
        await ctx.send("\n".join(f'<@{r.id}>' for r in srs),
                       allowed_mentions=discord.AllowedMentions.none)

    @commands.Cog.listener('on_member_update')
    async def sr_on_member_update(self, before: discord.Member, after: discord.Member):
        srs = await self.config.guild(before.guild).stickyroles()
        async with self.config.member(after).stickyroles() as member_srs:
            member_srs.clear()
            for role in after.roles:
                if role.id in srs:
                    member_srs.append(role.id)

    @commands.Cog.listener('on_member_join')
    async def sr_on_member_join(self, member: discord.Member):
        g_srs = await self.config.guild(member.guild).stickyroles()
        srs = await self.config.member(member).stickyroles()
        roles = [r for sr in srs if sr in g_srs and (r := member.guild.get_role(sr))]
        if roles:
            await member.add_roles(*roles, reason='Sticky Roles')
