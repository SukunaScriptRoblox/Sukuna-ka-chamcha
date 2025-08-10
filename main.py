import discord
from discord.ext import commands
import random
import json
import os
import aiohttp
import discord
import asyncio
from io import BytesIO
from PIL import Image
import requests
from keep_alive import keep_alive

curse_names = {
    "grade_1": ["Hanami", "Jogo", "Mahito"],
    "grade_2": ["Eso", "Kechizu"],
    "grade_3": ["Idle transfiguration"],
    "special_grade": ["Ryomen Sukuna", "Kenjaku"]
}
# Create intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create an instance of a bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Simple in-memory storage for user balances (in a real bot, you'd use a database)
user_balances = {}

# Global emoji storage - acts like "Nitro" storage
global_emojis = {}

OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

async def generate_chatgpt_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",  # Ya jo model use karna ho
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENROUTER_API_URL, headers=headers, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Error from OpenRouter: {resp.status}")
                return "Error aa gaya bhai, try kar phir se!"

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and message.author != bot.user:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        response = await generate_chatgpt_response(prompt)
        await message.channel.send(f"{message.author.mention} {response}")
    await bot.process_commands(message)
@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    
    # Cache all emojis from all servers (Nitro-like feature)
    await cache_all_emojis()
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) globally")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def cache_all_emojis():
    """Cache all emojis from all servers the bot is in - like Nitro!"""
    global global_emojis
    global_emojis.clear()
    
    total_emojis = 0
    for guild in bot.guilds:
        for emoji in guild.emojis:
            # Store by name (lowercase for easy searching)
            global_emojis[emoji.name.lower()] = {
                'name': emoji.name,
                'id': emoji.id,
                'guild_name': guild.name,
                'animated': emoji.animated
            }
            total_emojis += 1
    
    print(f"🎉 Cached {total_emojis} emojis from {len(bot.guilds)} servers! (Nitro mode activated)")

@bot.event
async def on_guild_join(guild):
    """Update emoji cache when bot joins a new server"""
    await cache_all_emojis()
    print(f"Joined {guild.name}! Updated emoji cache.")

@bot.event
async def on_guild_remove(guild):
    """Update emoji cache when bot leaves a server"""
    await cache_all_emojis()
    print(f"Left {guild.name}. Updated emoji cache.")

@bot.command()
async def spam(ctx, text: str, count: int = 5):
    """Spam messages (text command)."""
    if count > 10:  # Limit to prevent abuse
        await ctx.send("Count cannot exceed 10!")
        return
    for _ in range(count):
        await ctx.send(text)

@bot.tree.command(name="spam", description="Spam a message multiple times")
async def spam_slash(interaction: discord.Interaction, text: str, count: int = 5):
    """Spam messages (slash command)."""
    if count > 10:  # Limit to prevent abuse
        await interaction.response.send_message("Count cannot exceed 10!")
        return
    
    await interaction.response.send_message(f"Spamming '{text}' {count} times...")
    for i in range(count):
        await interaction.followup.send(f"{text} ({i+1}/{count})")

# Helper function to get user balance
def get_balance(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = 100  # Starting balance
    return user_balances[user_id]

def set_balance(user_id, amount):
    user_balances[user_id] = amount

# Coinflip command (text)
@bot.command()
async def coinflip(ctx, bet: int = 0):
    """Flip a coin, optionally with a bet."""
    user_id = ctx.author.id
    balance = get_balance(user_id)
    
    if bet > 0:
        if bet > balance:
            await ctx.send(f"You don't have enough coins! Your balance: {balance}")
            return
        if bet > 50:
            await ctx.send("Maximum bet is 50 coins!")
            return
    
    result = random.choice(["Heads", "Tails"])
    
    if bet > 0:
        won = random.choice([True, False])
        if won:
            winnings = bet
            new_balance = balance + winnings
            set_balance(user_id, new_balance)
            await ctx.send(f"🪙 **{result}!** You won {winnings} coins! New balance: {new_balance}")
        else:
            new_balance = balance - bet
            set_balance(user_id, new_balance)
            await ctx.send(f"🪙 **{result}!** You lost {bet} coins! New balance: {new_balance}")
    else:
        await ctx.send(f"🪙 **{result}!**")

# Coinflip slash command
@bot.tree.command(name="coinflip", description="Flip a coin, optionally with a bet")
async def coinflip_slash(interaction: discord.Interaction, bet: int = 0):
    """Flip a coin with optional betting."""
    user_id = interaction.user.id
    balance = get_balance(user_id)
    
    if bet > 0:
        if bet > balance:
            await interaction.response.send_message(f"You don't have enough coins! Your balance: {balance}")
            return
        if bet > 50:
            await interaction.response.send_message("Maximum bet is 50 coins!")
            return
    
    result = random.choice(["Heads", "Tails"])
    
    if bet > 0:
        won = random.choice([True, False])
        if won:
            winnings = bet
            new_balance = balance + winnings
            set_balance(user_id, new_balance)
            await interaction.response.send_message(f"🪙 **{result}!** You won {winnings} coins! New balance: {new_balance}")
        else:
            new_balance = balance - bet
            set_balance(user_id, new_balance)
            await interaction.response.send_message(f"🪙 **{result}!** You lost {bet} coins! New balance: {new_balance}")
    else:
        await interaction.response.send_message(f"🪙 **{result}!**")

# Balance command (text)
@bot.command()
async def bal(ctx):
    """Check your coin balance."""
    user_id = ctx.author.id
    balance = get_balance(user_id)
    await ctx.send(f"💰 {ctx.author.mention} Your balance: **{balance}** coins")

# Balance slash command
@bot.tree.command(name="bal", description="Check your coin balance")
async def bal_slash(interaction: discord.Interaction):
    """Check your coin balance."""
    user_id = interaction.user.id
    balance = get_balance(user_id)
    await interaction.response.send_message(f"💰 {interaction.user.mention} Your balance: **{balance}** coins")

# Daily reward command (text)
@bot.command()
async def daily(ctx):
    """Claim your daily coins."""
    user_id = ctx.author.id
    balance = get_balance(user_id)
    daily_amount = random.randint(10, 50)
    new_balance = balance + daily_amount
    set_balance(user_id, new_balance)
    await ctx.send(f"🎁 You claimed **{daily_amount}** daily coins! New balance: **{new_balance}**")

# Daily slash command
@bot.tree.command(name="daily", description="Claim your daily coins")
async def daily_slash(interaction: discord.Interaction):
    """Claim your daily coins."""
    user_id = interaction.user.id
    balance = get_balance(user_id)
    daily_amount = random.randint(10, 50)
    new_balance = balance + daily_amount
    set_balance(user_id, new_balance)
    await interaction.response.send_message(f"🎁 You claimed **{daily_amount}** daily coins! New balance: **{new_balance}**")

# Dice roll command (text)
@bot.command()
async def roll(ctx, sides: int = 6):
    """Roll a dice with specified sides (default 6)."""
    if sides < 2 or sides > 100:
        await ctx.send("Dice must have between 2 and 100 sides!")
        return
    result = random.randint(1, sides)
    await ctx.send(f"🎲 You rolled a **{result}** on a {sides}-sided dice!")

# Dice roll slash command
@bot.tree.command(name="roll", description="Roll a dice with specified sides")
async def roll_slash(interaction: discord.Interaction, sides: int = 6):
    """Roll a dice with specified sides."""
    if sides < 2 or sides > 100:
        await interaction.response.send_message("Dice must have between 2 and 100 sides!")
        return
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a **{result}** on a {sides}-sided dice!")

# 8-ball command (text)
@bot.command(name="8ball")
async def eightball(ctx, *, question: str):
    """Ask the magic 8-ball a question."""
    responses = [
        "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
        "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
        "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
        "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
        "Don't count on it", "My reply is no", "My sources say no",
        "Outlook not so good", "Very doubtful"
    ]
    response = random.choice(responses)
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {response}")

# 8-ball slash command
@bot.tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eightball_slash(interaction: discord.Interaction, question: str):
    """Ask the magic 8-ball a question."""
    responses = [
        "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
        "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
        "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
        "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
        "Don't count on it", "My reply is no", "My sources say no",
        "Outlook not so good", "Very doubtful"
    ]
    response = random.choice(responses)
    await interaction.response.send_message(f"🎱 **Question:** {question}\n**Answer:** {response}")

# Random number command (text)
@bot.command()
async def random_num(ctx, min_num: int = 1, max_num: int = 100):
    """Generate a random number between min and max."""
    if min_num >= max_num:
        await ctx.send("Minimum number must be less than maximum number!")
        return
    result = random.randint(min_num, max_num)
    await ctx.send(f"🔢 Random number between {min_num} and {max_num}: **{result}**")

# Random number slash command
@bot.tree.command(name="random", description="Generate a random number between min and max")
async def random_num_slash(interaction: discord.Interaction, min_num: int = 1, max_num: int = 100):
    """Generate a random number between min and max."""
    if min_num >= max_num:
        await interaction.response.send_message("Minimum number must be less than maximum number!")
        return
    result = random.randint(min_num, max_num)
    await interaction.response.send_message(f"🔢 Random number between {min_num} and {max_num}: **{result}**")

# Emoji ID command (text)
@bot.command()
async def id(ctx, emoji_name: str):
    """Get the ID of an emoji by its name."""
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server!")
        return
    
    # Search for exact emoji by name (case-insensitive)
    emoji = discord.utils.get(guild.emojis, name=emoji_name.lower())
    if not emoji:
        emoji = discord.utils.get(guild.emojis, name=emoji_name)
    
    if emoji:
        await ctx.send(f"📝 Emoji `:{emoji.name}:` ID: **{emoji.id}**\nFull format: `<:{emoji.name}:{emoji.id}>`")
    else:
        # Search for partial matches
        partial_matches = [e for e in guild.emojis if emoji_name.lower() in e.name.lower()]
        if partial_matches:
            matches_text = "\n".join([f"`:{e.name}:` (ID: {e.id})" for e in partial_matches[:10]])
            await ctx.send(f"❌ Exact match `:{emoji_name}:` not found! Did you mean:\n{matches_text}")
        else:
            await ctx.send(f"❌ No emoji matching `:{emoji_name}:` found in this server!\nUse `!list_emojis` to see all available emojis.")

# Emoji ID slash command (Now with Nitro-like global search!)
@bot.tree.command(name="id", description="Get the ID of an emoji by its name (searches all servers!)")
async def id_slash(interaction: discord.Interaction, emoji_name: str):
    """Get the ID of an emoji by its name from ALL servers (Nitro-like!)."""
    
    # First, search in global emoji cache (Nitro-like feature!)
    if emoji_name.lower() in global_emojis:
        emoji_data = global_emojis[emoji_name.lower()]
        animated_prefix = "a" if emoji_data['animated'] else ""
        full_format = f"<{animated_prefix}:{emoji_data['name']}:{emoji_data['id']}>"
        
        await interaction.response.send_message(
            f"🎉 **NITRO MODE:** Found `:{emoji_data['name']}:` from **{emoji_data['guild_name']}**!\n"
            f"📝 ID: **{emoji_data['id']}**\n"
            f"🔗 Full format: `{full_format}`\n"
            f"✨ You can use this emoji anywhere with `/use {emoji_data['id']} {emoji_data['name']}`!"
        )
        return
    
    # If not found globally, search for partial matches
    partial_matches = []
    for name, data in global_emojis.items():
        if emoji_name.lower() in name:
            partial_matches.append(data)
    
    if partial_matches:
        matches_text = "\n".join([f"`:{e['name']}:` from **{e['guild_name']}** (ID: {e['id']})" for e in partial_matches[:10]])
        await interaction.response.send_message(f"❌ Exact match not found! Did you mean:\n{matches_text}")
    else:
        await interaction.response.send_message(f"❌ No emoji matching `:{emoji_name}:` found across **{len(bot.guilds)}** servers!\nUse `/nitro_search` to search all available emojis.")

# Use emoji command (text)
@bot.command()
async def use(ctx, emoji_id: str, emoji_name: str = None):
    """Use an emoji by its ID."""
    try:
        # Try to get the emoji by ID
        emoji_id_int = int(emoji_id)
        emoji = bot.get_emoji(emoji_id_int)
        
        if emoji:
            await ctx.send(f"{emoji}")
        else:
            # If emoji not found, try to create the emoji format manually
            if emoji_name:
                await ctx.send(f"<:{emoji_name}:{emoji_id}>")
            else:
                await ctx.send(f"❌ Emoji with ID `{emoji_id}` not found!")
    except ValueError:
        await ctx.send("❌ Invalid emoji ID! Please provide a valid number.")

# Use emoji slash command (Enhanced Nitro-like usage!)
@bot.tree.command(name="use", description="Use any emoji by ID (works across all servers!)")
async def use_slash(interaction: discord.Interaction, emoji_id: str, emoji_name: str = None):
    """Use an emoji by its ID - works like Nitro across all servers!"""
    try:
        emoji_id_int = int(emoji_id)
        
        # First, try to get the emoji directly
        emoji = bot.get_emoji(emoji_id_int)
        
        if emoji:
            await interaction.response.send_message(f"{emoji} ✨")
            return
        
        # If not found directly, search in our global cache
        emoji_data = None
        for data in global_emojis.values():
            if data['id'] == emoji_id_int:
                emoji_data = data
                break
        
        if emoji_data:
            # Create the emoji format manually (works like Nitro!)
            animated_prefix = "a" if emoji_data['animated'] else ""
            emoji_format = f"<{animated_prefix}:{emoji_data['name']}:{emoji_id_int}>"
            await interaction.response.send_message(f"{emoji_format} 🎉 **(Nitro Mode: from {emoji_data['guild_name']})**")
        else:
            # Last resort: try with provided name
            if emoji_name:
                await interaction.response.send_message(f"<:{emoji_name}:{emoji_id}> 🤔 **(Attempting to use emoji)**")
            else:
                await interaction.response.send_message(f"❌ Emoji with ID `{emoji_id}` not found in any server I'm in!")
                
    except ValueError:
        await interaction.response.send_message("❌ Invalid emoji ID! Please provide a valid number.")

# List emojis command (text)
@bot.command()
async def list_emojis(ctx, search: str = None):
    """List all emojis in the server, optionally filter by search term."""
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server!")
        return
    
    emojis = guild.emojis
    if search:
        emojis = [e for e in emojis if search.lower() in e.name.lower()]
    
    if not emojis:
        await ctx.send("No emojis found!" if not search else f"No emojis found matching '{search}'!")
        return
    
    # Limit to 20 emojis per message to avoid spam
    emoji_list = emojis[:20]
    emoji_text = "\n".join([f"`:{e.name}:` (ID: {e.id})" for e in emoji_list])
    
    more_text = f"\n... and {len(emojis) - 20} more" if len(emojis) > 20 else ""
    await ctx.send(f"📝 **Emojis in {guild.name}:**\n{emoji_text}{more_text}")

# List emojis slash command
@bot.tree.command(name="list_emojis", description="List all emojis in the server")
async def list_emojis_slash(interaction: discord.Interaction, search: str = None):
    """List all emojis in the server, optionally filter by search term."""
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server!")
        return
    
    emojis = guild.emojis
    if search:
        emojis = [e for e in emojis if search.lower() in e.name.lower()]
    
    if not emojis:
        await interaction.response.send_message("No emojis found!" if not search else f"No emojis found matching '{search}'!")
        return
    
    # Limit to 20 emojis per message to avoid spam
    emoji_list = emojis[:20]
    emoji_text = "\n".join([f"`:{e.name}:` (ID: {e.id})" for e in emoji_list])
    
    more_text = f"\n... and {len(emojis) - 20} more" if len(emojis) > 20 else ""
    await interaction.response.send_message(f"📝 **Emojis in {guild.name}:**\n{emoji_text}{more_text}")

# NEW: Nitro-like global emoji search!
@bot.tree.command(name="nitro_search", description="🎉 Search ALL emojis across every server (like Nitro!)")
async def nitro_search_slash(interaction: discord.Interaction, search: str = None):
    """Search emojis across ALL servers the bot is in - like Discord Nitro!"""
    
    if not global_emojis:
        await interaction.response.send_message("❌ No emojis cached yet! Please wait for the bot to load.")
        return
    
    # Filter emojis based on search
    if search:
        filtered_emojis = []
        for name, data in global_emojis.items():
            if search.lower() in name:
                filtered_emojis.append(data)
    else:
        filtered_emojis = list(global_emojis.values())
    
    if not filtered_emojis:
        await interaction.response.send_message(f"❌ No emojis found matching '{search}'!")
        return
    
    # Limit to 15 emojis per message
    emoji_list = filtered_emojis[:15]
    emoji_text = "\n".join([
        f"`:{e['name']}:` from **{e['guild_name']}** (ID: {e['id']})" 
        for e in emoji_list
    ])
    
    total_servers = len(set(e['guild_name'] for e in global_emojis.values()))
more_text = f"\n... and {len(filtered_emojis) - 15} more" if len(filtered_emojis) > 15 else ""
    
    search_text = f" matching '{search}'" if search else ""
    await interaction.response.send_message(
        f"🎉 **NITRO MODE:** Found {len(filtered_emojis)} emojis{search_text} across **{total_servers}** servers!\n\n"
        f"{emoji_text}{more_text}\n\n"
        f"💡 Use `/use <emoji_id> <emoji_name>` to use any emoji anywhere!"
    )

# Auto emoji replacement feature!
@bot.tree.command(name="emoji_text", description="🎉 Convert text with :emoji: into actual emojis (Nitro-like!)")
async def emoji_text_slash(interaction: discord.Interaction, text: str):
    """Convert text with :emoji_name: into actual emojis from any server!"""
    import re
    
    # Find all :emoji_name: patterns
    emoji_pattern = r':(\w+):'
    emoji_matches = re.findall(emoji_pattern, text)
    
    if not emoji_matches:
        await interaction.response.send_message("❌ No emoji patterns found! Use format like `:rockcraft:` in your text.")
        return
    
    # Replace each emoji pattern with actual emoji
    result_text = text
    replacements_made = []
    
    for emoji_name in emoji_matches:
        if emoji_name.lower() in global_emojis:
            emoji_data = global_emojis[emoji_name.lower()]
            animated_prefix = "a" if emoji_data['animated'] else ""
            emoji_format = f"<{animated_prefix}:{emoji_data['name']}:{emoji_data['id']}>"
            
            result_text = result_text.replace(f":{emoji_name}:", emoji_format)
            replacements_made.append(f":{emoji_name}: → from **{emoji_data['guild_name']}**")
    
    if replacements_made:
        replacements_text = "\n".join(replacements_made)
        await interaction.response.send_message(
            f"🎉 **NITRO MODE ACTIVATED!**\n\n{result_text}\n\n"
            f"**Replacements made:**\n{replacements_text}"
        )
    else:
        await interaction.response.send_message(f"❌ None of the emojis found in my cache. Try `/nitro_search` to see available emojis!\n\nOriginal text: {text}")
 
# Say command
@bot.tree.command(name="say", description="Make the bot say something, optionally mentioning a user")
async def say_slash(interaction: discord.Interaction, text: str, user: discord.Member = None):
    """Make the bot say the provided text, optionally mentioning a user."""
    if user:
        message = f"{text} {user.mention}"
    else:
        message = text
    
    await interaction.response.send_message(message)

@bot.tree.command(name="help", description="Shows a list of available commands and their descriptions.")
async def help_slash(interaction: discord.Interaction):
    """Shows available commands."""
    embed = discord.Embed(title="Command List", description="Here are the available commands:", color=discord.Color.blue())

    for command in bot.commands:
        embed.add_field(name=f"!{command.name}", value=command.help or "No description available.", inline=False)

    for command in bot.tree.get_commands():  # Iterate through slash commands
        embed.add_field(name=f"/{command.name}", value=command.description or "No description available.", inline=False)

    await interaction.response.send_message(embed=embed)

favourite_emojis = {}

@bot.tree.command(name="favourite", description="Add an emoji to your favourites")
async def favourite_slash(interaction: discord.Interaction, emoji_name: str):
    """Add an emoji to favourites."""
    user_id = interaction.user.id
    
    # First, search in global emoji cache (Nitro-like feature!)
    if emoji_name.lower() in global_emojis:
        emoji_data = global_emojis[emoji_name.lower()]
        if user_id not in favourite_emojis:
            favourite_emojis[user_id] = []
        
        if emoji_data not in favourite_emojis[user_id]:
            favourite_emojis[user_id].append(emoji_data)
            await interaction.response.send_message(f"Added `:{emoji_data['name']}:` from **{emoji_data['guild_name']}** to your favourites!")
        else:
            await interaction.response.send_message(f"`:{emoji_data['name']}:` is already in your favourites!")
    else:
        await interaction.response.send_message(f"Emoji `:{emoji_name}:` not found. Use `/nitro_search` to find emojis.")

@bot.tree.command(name="show_fav", description="Show your favourite emojis in DM")
async def show_fav_slash(interaction: discord.Interaction):
    """Show favourite emojis in DM."""
    user_id = interaction.user.id
    
    if user_id not in favourite_emojis or not favourite_emojis[user_id]:
        await interaction.response.send_message("You have no favourite emojis yet! Use `/favourite` to add some.")
        return
    
    emoji_list = favourite_emojis[user_id]
    emoji_text = "\n".join([
        f"`:{e['name']}:` from **{e['guild_name']}** (ID: {e['id']})" 
        for e in emoji_list
    ])
    
    try:
        await interaction.user.send(f"📝 **Your Favourite Emojis:**\n{emoji_text}")
        await interaction.response.send_message("Sent your favourite emojis in a DM!")
    except discord.errors.Forbidden:
        await interaction.response.send_message("I can't send you DMs! Please enable them so I can show you your favourites.")

@bot.tree.command(name="dm", description="DM a user, even if they are not in the same server.")
async def dm_slash(interaction: discord.Interaction, user: discord.User, text: str):
    """DM a user, even if they are not in the same server."""
    try:
        await user.send(text)
        await interaction.response.send_message(f"✅ Successfully sent a DM to {user.name}#{user.discriminator}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ That user has DMs disabled or blocked the bot!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to send DM: {e}", ephemeral=True)

@bot.tree.command(name="invite", description="Invite a user to the server via DM")
async def invite_slash(interaction: discord.Interaction, user: discord.User):
    """Invite a user to the server via DM."""
    invite_message = (
        "**Join the Sukuna Anime Server. 😈**\n\n"
        "**__Why Join This Server?__**\n"
        "Because We Give You:\n\n"
        "_NSFW Bots 💀_\n"
        "_Best Giveaway🤑_\n"
        "_Anime World 😜_\n"
        "_Make friends. 😇_\n"
        "_more..._\n\n"
        "**Special ➕**\n\n"
        "> Minecraft Free Install ✅\n"
        "> Roblox Hacks ✅\n"
        "> Best Challenges ✅\n"
        "> Cosplay As Anime Characters ✅\n"
        "> Cool Roles ✅\n"
        "More...\n\n"
        "https://discord.gg/thUYXtBZDs"
    )
    try:
        await user.send(invite_message)
        await interaction.response.send_message(f"✅ Successfully sent an invite to {user.name}#{user.discriminator}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ That user has DMs disabled or blocked the bot!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to send DM: {e}", ephemeral=True)

@bot.tree.command(name="embaded", description="Make an embedded text")
async def embaded_slash(interaction: discord.Interaction, text: str):
    """Make an embedded text."""
    embed = discord.Embed(description=text, color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="giveaway_alert", description="Send a giveaway alert message.")
async def giveaway_alert_slash(interaction: discord.Interaction, message: str):
    """Send a giveaway alert."""
    await interaction.response.send_message(f"🎉 **GIVEAWAY ALERT!** 🎉\n\n{message}\n\n🎁 React to enter!")

@bot.tree.command(name="giveaway_won", description="Announce the winner of a giveaway.")
async def giveaway_won_slash(interaction: discord.Interaction, member: discord.Member):
    """Announce giveaway winner."""
    await interaction.response.send_message(f"🎉 Congratulations, {member.mention}! You won the giveaway! 🎉")


@bot.tree.command(name="show", description="Show a character's image.")
async def show_slash(interaction: discord.Interaction, character: str):
    """Show a character's image."""
    try:
        # Encode the character name for the URL
        encoded_character = character.replace(" ", "%20")
        
        # Construct the image URL (using a placeholder image API)
        image_url = f"https://api.jikan.moe/v4/characters?q={encoded_character}"  # Replace with actual API endpoint

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    data = await response.json()

                    if data['data']:
                        # Assuming the first result is the most relevant
                        character_data = data['data'][0]
                        image_url = character_data['images']['jpg']['image_url']
                        name = character_data['name']
                        about = character_data['about']
                        # Create an embed
                        embed = discord.Embed(title=name, description=about[:200] + "..." if about else "No description available.", color=discord.Color.blue())
                        embed.set_image(url=image_url)

                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message(f"❌ Character '{character}' not found.")
                else:
                    await interaction.response.send_message(f"❌ Failed to fetch character data. Status code: {response.status}")
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {e}")

@bot.tree.command(name="nsfw_tag", description="Tag a channel as NSFW")
async def nsfw_tag_slash(interaction: discord.Interaction, channel: discord.TextChannel):
    """Tag a channel as NSFW."""
    try:
        await channel.edit(nsfw=True)
        await interaction.response.send_message(f"✅ Successfully tagged {channel.mention} as NSFW!")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to edit that channel!")
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {e}")

def is_me():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == 1266464993499414598

    return commands.check(predicate)

@bot.tree.command(name="only_me", description="A command only you can use.")
@is_me()
async def only_me_slash(interaction: discord.Interaction):
    """A command only I can use."""
    await interaction.response.send_message("This command can only be used by you!")

@bot.command()
@commands.check(lambda ctx: ctx.author.id == 1266464993499414598)
async def only_me(ctx):
    await ctx.send("This command can only be used by you!")
@bot.tree.command(name="owo_prank", description="Give fake Owo to someone in Owo discord bot style")
async def owo_prank_slash(interaction: discord.Interaction, owo_price: int, user: discord.User):
    """Give fake Owo to someone in Owo discord bot style."""
    await interaction.response.send_message(f"OwO {user.mention} **has received** {owo_price} Owo! 😎🎊🎉")
# Global curse storage
bot.summoned_curses = []
bot.user_inventories = {}

async def summon_curse(channel):
    """Summons a curse in the given channel."""
    rarity = random.choices(
        ["grade_1", "grade_2", "grade_3", "special_grade"],
        weights=[0.4, 0.3, 0.2, 0.1],
        k=1
    )[0]

    curse_name = random.choice(curse_names[rarity])
    bot.summoned_curses.append(curse_name)
    await channel.send(f"⚠️ **{curse_name}** summoned! Type `!catch {curse_name}` to catch it!")
    return curse_name


async def give_arcane_xp(user, curse_name, channel):
    """Give Arcane XP based on the caught curse."""
    if curse_name == "Ryomen Sukuna":
        xp = 900
    elif curse_name in curse_names["special_grade"]:
        xp = random.randint(100, 200)
    else:
        xp = random.randint(1, 20)

    await channel.send(f"🔮 {user.mention} received {xp} Arcane XP for catching {curse_name}!")


# Slash command to start summoning
@bot.tree.command(name="start_jjk", description="Summon Jujutsu Kaisen curses in a channel.")
async def start_jjk_slash(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"Summoning JJK curses in {channel.mention} every 2-3 minutes...")

    async def summon_loop():
        while True:
            await asyncio.sleep(random.randint(120, 180))  # 2-3 minutes
            await summon_curse(channel)

    bot.loop.create_task(summon_loop())


# Text command to catch curse
@bot.command()
async def catch(ctx, *, curse_name: str):
    user_id = ctx.author.id

    if curse_name in bot.summoned_curses:
        bot.user_inventories.setdefault(user_id, []).append(curse_name)
        bot.summoned_curses.remove(curse_name)
        await ctx.send(f"{ctx.author.mention} caught {curse_name}! 🎉")
        await give_arcane_xp(ctx.author, curse_name, ctx.channel)
    else:
        await ctx.send(f"{ctx.author.mention} ❌ That curse is not active or already caught!")


@bot.command()
async def inventory(ctx):
    """Check your inventory of caught curses."""
    user_id = ctx.author.id
    if user_id in bot.user_inventories and bot.user_inventories[user_id]:
        curses = ", ".join(bot.user_inventories[user_id])
        await ctx.send(f"{ctx.author.mention} Your inventory: {curses}")
    else:
        await ctx.send(f"{ctx.author.mention} Your inventory is empty! Catch some curses with `!catch`!")

@bot.tree.command(name="poll", description="Create a poll with reactions")
async def poll_slash(interaction: discord.Interaction, msg: str, emoji1: str, emoji2: str, opinion: str, emoji3: str = None, emoji4: str = None, emoji5: str = None, emoji6: str = None, emoji7: str = None):
    """Create a poll with reactions."""
    await interaction.response.send_message(msg)
    message = await interaction.original_response()
    
    try:
        await message.add_reaction(emoji1)
        await message.add_reaction(emoji2)
        if emoji3:
            await message.add_reaction(emoji3)
        if emoji4:
            await message.add_reaction(emoji4)
        if emoji5:
            await message.add_reaction(emoji5)
        if emoji6:
            await message.add_reaction(emoji6)
        if emoji7:
            await message.add_reaction(emoji7)
    except discord.errors.NotFound:
        await interaction.followup.send("Emoji not found. Please use valid emojis.")
    except discord.errors.HTTPException as e:
        await interaction.followup.send(f"Failed to add reaction: {e}")
@bot.tree.command(name="react", description="React to a message with an emoji")
async def react_slash(interaction: discord.Interaction, message_id: str, emoji: str):
    """React to a message with an emoji."""
    try:
        message_id_int = int(message_id)
        channel = interaction.channel
        message = await channel.fetch_message(message_id_int)
        await message.add_reaction(emoji)
        await interaction.response.send_message("✅ Reaction added successfully!", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID. Please provide a valid number.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("❌ Message not found. Please provide a valid message ID from this channel.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to add reactions to that message.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to add reaction: {e}", ephemeral=True)
# Run the bot with the toke (replace 'YOUR_TOKEN_HERE' with your bot's token)
keep_alive()
bot.run('MTQwNDEyMjAzMjk0NTUwMDMwMQ.G8cQJo.GCE3jhDMawLIgyGrWHTFaHFN-8VkKPnULSBSw0')
