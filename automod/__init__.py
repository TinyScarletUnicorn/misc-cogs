from .automod import AutoMod

__red_end_user_data_statement__ = "This cog stores id of users manually marked as problematic."


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
