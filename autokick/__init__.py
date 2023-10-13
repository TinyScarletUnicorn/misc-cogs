from .autokick import AutoKick

__red_end_user_data_statement__ = "No personal data is stored."


async def setup(bot):
    ak = AutoKick(bot)
    await bot.add_cog(ak)
    await ak.kick_users()
