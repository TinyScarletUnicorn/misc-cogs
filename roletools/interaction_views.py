import discord
from redbot.core import app_commands


class ZRAssign(discord.ui.Select):
    def __init__(self, member: discord.Member, roles: list[discord.Role]):
        self.member = member
        super().__init__(
            placeholder="Select an option",
            max_values=1,
            min_values=1,
            options=[discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
        )

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, id=int(self.options[0].value))
        if role in self.member.roles:
            return await interaction.response.send_message(f"{self.member.mention} already has the {role.mention} role.", ephemeral=True)
        try:
            await self.member.add_roles(role, reason="ZombieRole Assignment")
            await interaction.response.send_message(f"{self.member.mention} has been assigned the {role.mention} role.", ephemeral=True)
        except discord.Forbidden as e:
            print(e)
            await interaction.response.send_message("Unable to assign role. Please ensure that the role is lower than the bot's highest role.", ephemeral=True)

class ZRAssignView(discord.ui.View):
    def __init__(self, *, member: discord.Member, roles: list[discord.Role], timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(ZRAssign(member, roles))