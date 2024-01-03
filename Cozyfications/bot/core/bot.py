import os
import platform
import sys
import traceback

import discord
from aiohttp import ClientSession

from Cozyfications import secrets
from Cozyfications.bot import core


class Cozyfications(discord.Bot):
    QUEUE = []

    def __init__(self) -> None:
        super().__init__(
            activity=discord.CustomActivity("/help"),
            help_command=None,
            intents=discord.Intents(
                guilds=True,
                members=True,
                messages=True
            ),
            owner_ids=[810863994985250836, 672768917885681678],
            debug_guilds=[1018128160962904114]
        )

        self.on_ready_fired: bool = False

        self.errors_webhook: discord.Webhook | None = None
        self.color = 0xE0B484

        self.new_subscriptions: int = 0
        self.delete_subscriptions: int = 0
        self.subscriptions: dict[str, callable] = {
            "channel.update": core.Callbacks.update,
            "stream.online": core.Callbacks.online,
            "stream.offline": core.Callbacks.offline
        }

        self.port: int = 6001
        self.url: str | None = None
        # TODO: Fix Twitch API
        #  self.hook: EventSub | None = None
        #  self.ttv: TwitchAPI | None = None

        for filename in os.listdir("Cozyfications/bot/cogs"):
            if filename.endswith(".py"):
                self.load_cog(f"Cozyfications.bot.cogs.{filename[:-3]}")

    @property
    def http_session(self) -> ClientSession:
        return self.http._HTTPClient__session

    def load_cog(self, cog: str) -> None:
        try:
            self.load_extension(cog)
        except Exception as e:
            e = getattr(e, "original", e)
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    async def on_ready(self):
        if self.on_ready_fired:
            return
        self.on_ready_fired = True

        self.errors_webhook: discord.Webhook = discord.Webhook.from_url(
            url=secrets.Discord.ERRORS_WEBHOOK,
            session=self.http_session,
            bot_token=self.http.token,
        )

        self.add_view(view=core.ConfirmDialog())

        msg: str = f"""{self.user.name} is online now!
            BotID: {self.user.id}
            Ping: {round(self.latency * 1000)} ms
            Python Version: {platform.python_version()}
            PyCord API version: {discord.__version__}"""
        print(f"\n\n{msg}\n\n")

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
        if isinstance((error := error.original), discord.HTTPException):
            description = f"""An HTTP exception has occurred:
            {error.status} {error.__class__.__name__}"""
            if error.text:
                description += f": {error.text}"
            return await ctx.respond(
                embed=discord.Embed(
                    title="HTTP Exception",
                    description=description,
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
            )

        await ctx.respond(embed=discord.Embed(
            title="Error",
            description="An unexpected error has occurred and I've notified my developers.",
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow()
        ), ephemeral=True)
        if ctx.guild is not None:
            guild = f"`{ctx.guild.name} ({ctx.guild_id})`"
        else:
            guild = "None (DMs)"
        formatted_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        error_embed = discord.Embed(
            title=error.__class__.__name__,
            description=str(error),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        error_embed.add_field(name="Command:", value=f"`/{ctx.command.qualified_name}`", inline=True)
        error_embed.add_field(name="Guild:", value=f"`{guild}`", inline=True)
        error_embed.add_field(name="Error:", value=f"```py\n{formatted_error}```", inline=False)
        if len(error_embed.fields[2].value) > 1024:
            error_embed.remove_field(2)
            error_embed.add_field(
                name="Error:",
                value=f"```py\n{formatted_error[:1011]}```",
                inline=False
            )
            for i in range(1011, len(formatted_error), 1011):
                error_embed.add_field(
                    name="",
                    value=f"```py\n{formatted_error[i:i + 1011]}```",
                    inline=False
                )
        return await self.errors_webhook.send(
            embed=error_embed,
            avatar_url=self.user.display_avatar.url
        )

    async def on_error(self, event: str, *args, **kwargs):
        _, error, error_traceback = sys.exc_info()
        formatted_error = ''.join(traceback.format_exception(type(error), error, error_traceback))
        error_embed = discord.Embed(
            title=error.__class__.__name__,
            description=str(error),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        error_embed.add_field(name="Event:", value=f"```py\n{event}```", inline=True)
        error_embed.add_field(name="Args:", value=f"```py\n{args}```", inline=True)
        error_embed.add_field(name="KwArgs:", value=f"```py\n{kwargs}```", inline=True)
        error_embed.add_field(name="Error:", value=f"```py\n{formatted_error}```", inline=False)
        if len(error_embed.fields[2].value) > 1024:
            error_embed.remove_field(2)
            error_embed.add_field(
                name="Error:",
                value=f"```py\n{formatted_error[:1011]}```",
                inline=False
            )
            for i in range(1011, len(formatted_error), 1011):
                error_embed.add_field(
                    name="",
                    value=f"```py\n{formatted_error[i:i + 1011]}```",
                    inline=False
                )
        return await self.errors_webhook.send(
            embed=error_embed,
            avatar_url=self.user.display_avatar.url
        )

    def run(self):
        super().run(secrets.Discord.TOKEN)