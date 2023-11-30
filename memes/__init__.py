from .memes import Memes

__red_end_user_data_statement__ = "All stored data is anonymized."


async def setup(bot):
    await bot.add_cog(Memes(bot))
