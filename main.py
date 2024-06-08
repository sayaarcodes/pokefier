# Copyright (C) 2024 [Sayaar] (Pokefier)

import discord
import asyncio
from discord.ext import commands
import random
import json

from pkidentify import Pokefier
from captcha_solver import verify

# Initialize Pokefier instance
pokefier = Pokefier()

# Configuration 
POKETWO_ID = 716390085896962058  # Assuming ID is stored in an environment variable
WHITELISTED_CHANNELS = []
LANGUAGES = ["english"]

owner_id = 69420

def is_spawn_message(message, whitelisted_channels):
    """
    Checks if the message is a spawn message from Poketwo in a whitelisted channel.

    Args:
        message (discord.Message): The message to check.
        whitelisted_channels (list): The list of whitelisted channel IDs.

    Returns:
        bool: True if the message is a spawn message, False otherwise.
    """
    return (message.author.id == POKETWO_ID and
            message.channel.id in whitelisted_channels and
            len(message.embeds) > 0 and
            "wild pokémon has appeared".lower() in message.embeds[0].title.lower())

def is_captcha_message(message, whitelisted_channels, id):
    """
    Checks if the message contains a captcha challenge from Poketwo in a whitelisted channel.

    Args:
        message (discord.Message): The message to check.
        whitelisted_channels (list): The list of whitelisted channel IDs.
        id (int): The user ID to verify against.

    Returns:
        bool: True if the message is a captcha challenge, False otherwise.
    """
    return (message.author.id == POKETWO_ID and
            message.channel.id in whitelisted_channels and
            f"https://verify.poketwo.net/captcha/{id}" in message.content)

class Autocatcher(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, self_bot=False, guild_subscription_options=discord.GuildSubscriptionOptions.off())
        self.whitelisted_channels = WHITELISTED_CHANNELS
        self.languages = LANGUAGES
        self.pokemon_data = self.load_pokemon_data()

    def solve_captcha(self):
        """
        Solves the captcha challenge by calling the verify function.

        Returns:
            bool: True if the captcha was solved successfully.
        """
        verify(self)
        return True

    def load_pokemon_data(self):
        """
        Loads Pokémon data from a JSON file.

        Returns:
            dict: The loaded Pokémon data.
        """
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)

    async def get_alternate_pokemon_name(self, name, languages=LANGUAGES):
        """
        Retrieves an alternate name for a Pokémon in the specified languages.

        Args:
            name (str): The Pokémon name to find alternates for.
            languages (list): The list of languages to consider.

        Returns:
            str: The alternate Pokémon name, or the original name if no alternate is found.
        """
        pokemon = next(
            (p for p in self.pokemon_data if p["name"].lower() == name.lower()), None
        )

        if pokemon:
            alternate_names = [
                alt_name
                for alt_name in pokemon.get("altnames", [])
                if alt_name.get("language").lower() in languages
            ]

            if alternate_names:
                return random.choice(alternate_names)["name"].lower()

        return name.lower()
    
async def run_autocatcher(token):
    """
    Runs the autocatcher bot.

    Args:
        token (str): The token to authenticate the bot.

    Returns:
        None
    """
    bot = Autocatcher()

    @bot.event
    async def on_ready():
        """
        Event handler for when the bot is ready.
        """
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")

        # Set command prefix dynamically after login for self-bot safety
        bot.command_prefix = f"<@{bot.user.id}> "

    @bot.command()
    async def ping(ctx):
        """
        Responds with 'Pong!' to check if the bot is responsive.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        await ctx.send("Pong!")

    @bot.command()
    async def channeladd(ctx, *channel_ids):
        """
        Adds a channel ID to the whitelist.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            channel_ids (str): A list of channel IDs separated by spaces.
        """
        if not channel_ids:
            await ctx.reply("`You must provide at least one channel ID. Separate multiple IDs with spaces.`")
            return

        message = "```\n"

        for channel_id_str in channel_ids:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await ctx.reply(f"Invalid channel ID: `{channel_id_str}`. Please provide a valid numeric channel ID.")
                continue

            if channel_id in bot.whitelisted_channels:
                message += f"Channel ID: {channel_id} is already whitelisted\n"
            else:
                bot.whitelisted_channels.append(channel_id)
                message += f"Channel ID: {channel_id} whitelisted\n"

        message += "```"
        await ctx.send(message)

    @bot.command()
    async def channelremove(ctx, *channel_ids):
        """
        Removes a channel ID from the whitelist.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            channel_ids (str): A list of channel IDs separated by spaces.
        """
        if not channel_ids:
            await ctx.reply("`You must provide at least one channel ID. Separate multiple IDs with spaces.`")
            return

        message = "```\n"

        for channel_id_str in channel_ids:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await ctx.reply(f"Invalid channel ID: `{channel_id_str}`. Please provide a valid numeric channel ID.")
                continue

            if channel_id in bot.whitelisted_channels:
                bot.whitelisted_channels = [
                    ch_id for ch_id in bot.whitelisted_channels if ch_id != channel_id
                ]
                message += f"Channel ID: {channel_id} removed from whitelist\n"
            else:
                message += f"Channel ID: {channel_id} is not whitelisted\n"

        message += "```"
        await ctx.send(message)

    @bot.command()
    async def languageadd(ctx, *languages):
        """
        Adds a language to use while catching Pokemon.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            languages (str): A list of languages separated by spaces.
        """
        if not languages:
            await ctx.reply("`You must provide at least one language. Separate multiple languages with spaces.`")
            return

        message = "```\n"
        valid_languages = ["english", "french", "german", "japanese"]

        for language in languages:
            if language.lower() not in valid_languages:
                await ctx.reply(f"Invalid language: `{language}`. Please provide a valid language used by Poketwo.")
                continue

            if language.lower() in bot.languages:
                message += f"Language: {language} is already added\n"
            else:
                bot.languages.append(language.lower())
                message += f"Language: {language} added\n"

        message += "```"
        await ctx.send(message)

    @bot.command()
    async def languageremove(ctx, *languages):
        """
        Removes a language from the list of languages used while catching Pokemon.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            languages (str): A list of languages separated by spaces.
        """
        if not languages:
            await ctx.reply("`You must provide at least one language. Separate multiple languages with spaces.`")
            return

        message = "```\n"
        valid_languages = ["english", "french", "german", "japanese"]

        for language in languages:
            if language.lower() not in valid_languages:
                await ctx.reply(f"Invalid language: `{language}`. Please provide a valid language used by Poketwo.")
                continue

            if language.lower() in bot.languages:
                bot.languages = [
                    lang for lang in bot.languages if lang != language
                ]
                message += f"Language: {language} removed\n"
            else:
                message += f"Language: {language} is not added\n"

        message += "```"
        await ctx.send(message)

    @bot.command()
    async def inc(ctx):
        """
        Buys incense for the bot if the author is the owner.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        if ctx.author.id != owner_id:
            return
        else:
            await ctx.send("<@716390085896962058> incense buy")
            resp = await bot.wait_for("message")

            await resp.components[2].children[0].click()
            await ctx.send("Yes")

            resp = await bot.wait_for("message", check=lambda m: m.author.id == '716390085896962058')

            if "You don't have enough" in resp.content:
                await ctx.send("<@716390085896962058> buy shards 50")

                resp = await bot.wait_for("message", check=lambda m: m.author.id == '716390085896962058')
                await resp.components[0].children[0].click()

                await ctx.send("<@716390085896962058> incense buy")
                resp = await bot.wait_for("message", check=lambda m: m.author.id == '716390085896962058')

                await resp.components[2].children[0].click()

    @bot.command()
    async def config(ctx):
        """
        Displays the current bot configuration.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        message = f"```PREFIX: {bot.command_prefix}\nOWNER_ID: {owner_id}\nWHITELISTED_CHANNELS = {bot.whitelisted_channels}\nLANGUAGES = {bot.languages}```"
        await ctx.reply(message)

    @bot.command()
    async def say(ctx, *, message):
        """
        Sends a message if the author is the owner.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            message (str): The message to send.
        """
        if ctx.message.author.id != owner_id:
            return
        else:
            await ctx.send(message)

    @bot.event
    async def on_message(message):
        """
        Event handler for when a message is received.

        Args:
            message (discord.Message): The received message.
        """
        await bot.process_commands(message)

        # Check for specific message conditions (author, channel, embed content)
        if is_spawn_message(message, bot.whitelisted_channels) and bot.verified:
            pokemon_image = message.embeds[0].image.url

            # Use Pokefier to predict Pokemon name
            predicted_pokemons = await pokefier.predict_pokemon_from_url(pokemon_image)
            print(predicted_pokemons)

            predicted_pokemon = max(predicted_pokemons, key=lambda x: x[1])

            name = predicted_pokemon[0]
            score = predicted_pokemon[1]

            if score > 60.0:
                # Get alternative pokemon name
                alt_name = await bot.get_alternate_pokemon_name(name, languages=bot.languages)

                # Send message mentioning the bot with the alternative name
                await message.channel.send(f"<@716390085896962058> c {alt_name}")

        if is_captcha_message(message, bot.whitelisted_channels, bot.user.id):
            bot.verified = False
            bot.solve_captcha()

    await bot.start(token)

async def main():
    """
    Main function to run the autocatcher bot.

    Returns:
        None
    """
    tokens = []

    tasks = [run_autocatcher(token) for token in tokens]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
