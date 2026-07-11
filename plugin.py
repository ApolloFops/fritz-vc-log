import discord
from discord.channel import TextChannel
from discord.ext import commands
from discord.commands import SlashCommandGroup

from scripts.tools import journal

from .config import LOG_COMPONENT
from .database import VCLogDatabase

CONTEXTS = {discord.InteractionContextType.guild, discord.InteractionContextType.private_channel}
INTEGRATION_TYPES = {discord.IntegrationType.guild_install}

database = VCLogDatabase()


class VCJoinLeaveView(discord.ui.DesignerView):
	def __init__(self, member: discord.Member, channel: discord.VoiceChannel | discord.StageChannel, joined: bool):
		super().__init__(timeout=None)

		container = discord.ui.Container(colour=discord.Colour.green() if joined else discord.Colour.red())
		super().add_item(container)

		title_text = discord.ui.TextDisplay(f"### Member {'Joined' if joined else 'Left'} VC")
		container.add_item(title_text)

		body_text = discord.ui.TextDisplay(f"Member {member.mention} {'joined' if joined else 'left'} {channel.jump_url}")
		container.add_item(body_text)


class VCLog(commands.Cog):
	command_group = SlashCommandGroup("vclog", "VC log", contexts=CONTEXTS, integration_types=INTEGRATION_TYPES)

	def __init__(self, bot: discord.Bot):
		self.bot = bot

	@command_group.command(name="set_channel", description="Set what channel VC log messages should be sent in for this server", contexts=CONTEXTS, integration_types=INTEGRATION_TYPES)
	@commands.has_permissions(administrator=True)
	async def set_channel(self, ctx, channel: TextChannel):
		database.set_channel(ctx.guild_id, channel.id)

		await ctx.respond(f"Set the VC log channel to {channel.jump_url}")

	@command_group.command(name="remove_channel", description="Removes the VC log channel for this server.", contexts=CONTEXTS, integration_types=INTEGRATION_TYPES)
	@commands.has_permissions(administrator=True)
	async def remove_channel(self, ctx):
		database.remove_channel(ctx.guild_id)

		await ctx.respond("VC log channel removed")

	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
		if (before.channel is None) and (after.channel is not None):
			# User joined VC
			await self.send_join_leave_message(member, after.channel, True)
		elif (before.channel is not None) and (after.channel is None):
			# User left VC
			await self.send_join_leave_message(member, before.channel, False)

	async def send_join_leave_message(self, member: discord.Member, channel: discord.VoiceChannel | discord.StageChannel, joined: bool):
		guild_id = member.guild.id
		log_channel_id = database.get_channel(guild_id)

		if log_channel_id:
			server = self.bot.get_guild(guild_id)

			log_channel = server.get_channel(log_channel_id)
			if log_channel is None:
				journal.log(f"Couldn't find channel {log_channel_id} in cache, fetching from Discord", 7, component=LOG_COMPONENT)
				log_channel = await server.fetch_channel(log_channel_id)

			await log_channel.send(view=VCJoinLeaveView(member, channel, joined), allowed_mentions=discord.AllowedMentions(users=False, roles=False))


def setup(bot):
	bot.add_cog(VCLog(bot))


def teardown(bot):
	bot.remove_cog("VCLog")
