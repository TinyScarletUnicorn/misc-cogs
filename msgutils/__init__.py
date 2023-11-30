from .msgutils import MsgUtils

__red_end_user_data_statement__ = "No personal data is stored."


async def setup(bot):
    await bot.add_cog(MsgUtils(bot))
