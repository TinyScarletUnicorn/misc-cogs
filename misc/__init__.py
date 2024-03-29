from .baduser import BadUser

__red_end_user_data_statement__ = "All users last 10 messages are stored in memory, and when a user is marked as problematic, their last 10 messages are stored perminently for logging purposes."


async def setup(bot):
    await bot.add_cog(BadUser(bot))
