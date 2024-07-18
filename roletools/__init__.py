from .roletools import RoleTools

__red_end_user_data_statement__ = "The most recent answer in each channel is stored."


async def setup(bot):
    await bot.add_cog(RoleTools(bot))
