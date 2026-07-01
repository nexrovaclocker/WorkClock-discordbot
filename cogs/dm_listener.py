import discord
from discord.ext import commands
from config import config

class DMListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # If it's a DM
        if isinstance(message.channel, discord.DMChannel):
            standup_channel = self.bot.get_channel(config.STANDUP_CHANNEL_ID)
            if standup_channel:
                embed = discord.Embed(
                    title=f"🌙 Nightly Update from {message.author.display_name}",
                    description=message.content,
                    color=0x9B59B6
                )
                await standup_channel.send(embed=embed)
                await message.channel.send("✅ Got it! I've logged your nightly update to the team.")

async def setup(bot: commands.Bot):
    await bot.add_cog(DMListener(bot))
