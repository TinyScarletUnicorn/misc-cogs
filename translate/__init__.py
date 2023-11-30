import json
from pathlib import Path

from .translate import Translate

with open(Path(__file__).parent / "info.json") as file:
    __red_end_user_data_statement__ = json.load(file)['end_user_data_statement']


async def setup(bot):
    await bot.add_cog(Translate(bot))
