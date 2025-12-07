import os
import discord
from discord.ext import commands
from discord import app_commands
import json

# ------------------------
# Load token from secret
# ------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

# ------------------------
# Bot setup
# ------------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------
# Data storage
# ------------------------
DATA_FILE = "data/players.json"

def load_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ------------------------
# Bot Ready Event
# ------------------------
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced ({len(synced)})")
    except Exception as e:
        print("Error syncing commands:", e)

# ============================================================
# PLAYER / CHARACTER COMMANDS
# ============================================================

@bot.tree.command(name="register", description="Register as a Perfect Draw player.")
async def register(interaction: discord.Interaction):
    data = load_data()
    user = str(interaction.user.id)

    if user in data:
        await interaction.response.send_message("You are already registered!", ephemeral=True)
        return

    data[user] = {
        "passion": 0,
        "skill": 0,
        "friendship": 0,
        "baggage": [],
        "deck": [],
        "hand": []
    }

    save_data(data)
    await interaction.response.send_message("You are now registered!", ephemeral=True)

# ============================================================
# ADD A CARD TO DECK (with image)
# ============================================================

@bot.tree.command(name="addcard", description="Add a card to your deck.")
@app_commands.describe(
    name="The name/title of the card",
    strength="Weak, Normal, or Strong",
    type="Warrior, Item, or Invocation",
    image="Upload a picture for the card"
)
async def addcard(interaction: discord.Interaction, name: str, strength: str, type: str, image: discord.Attachment):
    data = load_data()
    user = str(interaction.user.id)

    if user not in data:
        await interaction.response.send_message("You must register first: `/register`", ephemeral=True)
        return
    
    # Save card info
    card = {
        "name": name,
        "strength": strength,
        "type": type,
        "image_url": image.url
    }

    data[user]["deck"].append(card)
    save_data(data)

    embed = discord.Embed(title="Card Added", description=f"**{name}** added to your deck.")
    embed.set_image(url=image.url)

    await interaction.response.send_message(embed=embed)

# ============================================================
# VIEW DECK
# ============================================================

@bot.tree.command(name="deck", description="View your deck.")
async def deck(interaction: discord.Interaction):
    data = load_data()
    user = str(interaction.user.id)
    
    if user not in data or len(data[user]["deck"]) == 0:
        await interaction.response.send_message("You have no cards in your deck.", ephemeral=True)
        return

    message = "**Your Deck:**\n"
    for c in data[user]["deck"]:
        message += f"- **{c['name']}** ({c['type']} | {c['strength']})\n"

    await interaction.response.send_message(message)

# ============================================================
# SEARCH CARD BY NAME
# ============================================================

@bot.tree.command(name="card", description="Search for a card in your deck.")
@app_commands.describe(name="The card's name")
async def card(interaction: discord.Interaction, name: str):
    data = load_data()
    user = str(interaction.user.id)

    if user not in data:
        await interaction.response.send_message("You must register first: `/register`", ephemeral=True)
        return

    for c in data[user]["deck"]:
        if c["name"].lower() == name.lower():
            embed = discord.Embed(
                title=c["name"],
                description=f"{c['type']} — **{c['strength']}**"
            )
            embed.set_image(url=c["image_url"])
            await interaction.response.send_message(embed=embed)
            return

    await interaction.response.send_message("Card not found.", ephemeral=True)

# ============================================================
# PERFECT DRAW BASIC ROLL COMMAND
# ============================================================

import random

@bot.tree.command(name="roll", description="Roll a Perfect Draw move (2d6 + stat).")
@app_commands.describe(stat="Passion, Skill, or Friendship")
async def roll(interaction: discord.Interaction, stat: str):
    data = load_data()
    user = str(interaction.user.id)

    if user not in data:
        await interaction.response.send_message("Register first: `/register`", ephemeral=True)
        return

    if stat.lower() not in ["passion", "skill", "friendship"]:
        await interaction.response.send_message("Invalid stat.", ephemeral=True)
        return

    base = random.randint(1, 6) + random.randint(1, 6)
    modifier = data[user][stat.lower()]
    total = base + modifier

    result = f"You rolled **{base} + {modifier} = {total}**"

    await interaction.response.send_message(result)

# ============================================================
# Run the bot
# ============================================================
bot.run(TOKEN)
