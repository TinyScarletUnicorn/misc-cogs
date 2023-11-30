from .shutup import ShutUp

__red_end_user_data_statement__ = "Todo lists are stored."


async def setup(bot):
    await bot.add_cog(ShutUp(bot))
    pass
