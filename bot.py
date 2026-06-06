import os
import json
import random
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

# --- DYNAMIC CONFIGURATION LOADER ---
WORDS_DATABASE = {}
CATEGORIES_DIR = "words"

def load_categories():
    """Scans the categories directory and loads all JSON word files."""
    global WORDS_DATABASE
    WORDS_DATABASE.clear()
    
    # Create the directory if it doesn't exist yet
    if not os.path.exists(CATEGORIES_DIR):
        os.makedirs(CATEGORIES_DIR)
        print(f"⚠️ Created missing '{CATEGORIES_DIR}' directory. Please add JSON files.")
        return

    # Loop through all files in the folder
    for filename in os.listdir(CATEGORIES_DIR):
        if filename.endswith(".json"):
            category_name = filename[:-5].lower() # Removes '.json' from filename
            file_path = os.path.join(CATEGORIES_DIR, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    word_pairs = json.load(f)
                    if isinstance(word_pairs, list) and len(word_pairs) > 0:
                        WORDS_DATABASE[category_name] = word_pairs
                        print(f"✅ Loaded category '{category_name}' with {len(word_pairs)} pairs.")
                    else:
                        print(f"❌ Skipped '{filename}': Invalid format (must be a non-empty list).")
            except Exception as e:
                print(f"❌ Error reading '{filename}': {e}")

# Initial load at startup
load_categories()


class UndercoverBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")
        try:
            synced = await self.tree.sync()
            print(f"Success: {len(synced)} slash commands synced.")
        except Exception as e:
            print(f"Error syncing commands: {e}")

bot = UndercoverBot()

# --- INTERACTIVE INTERFACE ---
class GameSetupView(discord.ui.View):
    def __init__(self, category: str, nb_undercover: int, nb_white: int):
        super().__init__(timeout=180)
        self.category = category
        self.nb_undercover = nb_undercover
        self.nb_white = nb_white

    @discord.ui.select(
        cls=discord.ui.UserSelect, 
        placeholder="Select all the players for this game...", 
        min_values=3, 
        max_values=25
    )
    async def select_players(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        game_members = [m for m in select.values if isinstance(m, discord.Member) and not m.bot]
        total_players = len(game_members)
        total_special_roles = self.nb_undercover + self.nb_white
        
        if total_players < 3:
            await interaction.response.send_message("❌ You need at least 3 human players!", ephemeral=True)
            return
            
        if total_special_roles >= total_players:
            await interaction.response.send_message(
                f"❌ Invalid setup: {total_special_roles} special roles for only {total_players} players.", 
                ephemeral=True
            )
            return

        select.disabled = True
        await interaction.response.edit_message(content="🎲 Distributing secret roles...", view=self)

        # Pick ONE random pair from the selected category list
        word_pair = random.choice(WORDS_DATABASE[self.category])
        civil_word, undercover_word = word_pair
        
        random.shuffle(game_members)
        undercover_players = game_members[:self.nb_undercover]
        mr_white_players = game_members[self.nb_undercover : self.nb_undercover + self.nb_white]
        civil_players = game_members[self.nb_undercover + self.nb_white :]

        roles_summary = f"🕵️ {self.nb_undercover} Undercover | 🤍 {self.nb_white} Mr. White | 🧑‍🌾 {len(civil_players)} Civilians"
        await interaction.followup.send(
            f"🎮 **The Undercover game has started!**\n"
            f"📂 Category: `{self.category.capitalize()}`\n"
            f"⚙️ Configuration: `{roles_summary}`\n"
            f"👥 Players ({total_players}): {', '.join([m.mention for m in game_members])}\n"
            f"👉 Check your DMs!",
            ephemeral=False
        )

        for u_player in undercover_players:
            try:
                await u_player.send(f"Your secret word is: **{undercover_word}**.")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Could not send DM to {u_player.mention}.")

        for w_player in mr_white_players:
            try:
                await w_player.send(f"🤍 **You are MR. WHITE!**\nYou have **NO** secret word. Try to blend in!")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Could not send DM to {w_player.mention}.")

        for c_player in civil_players:
            try:
                await c_player.send(f"Your secret word is: **{civil_word}**.")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Could not send DM to {c_player.mention}.")


# --- MAIN SLASH COMMAND ---
@bot.tree.command(name="undercover", description="Open the setup menu to launch an Undercover game.")
@app_commands.describe(
    undercovers="Number of Undercovers (Default: 1)",
    mr_whites="Number of Mr. Whites (Default: 0)",
    category="Optional: Word category. If left empty, a random file will be picked."
)
async def undercover(
    interaction: discord.Interaction, 
    undercovers: int = 1, 
    mr_whites: int = 0, 
    category: Optional[str] = None
):
    if undercovers < 1 or mr_whites < 0:
        await interaction.response.send_message("❌ Invalid settings.", ephemeral=True)
        return

    # Emergency check if no JSON files were loaded at all
    if not WORDS_DATABASE:
        await interaction.response.send_message("❌ No categories found in the server folder. Please add JSON files.", ephemeral=True)
        return

    if category is None:
        chosen_category = random.choice(list(WORDS_DATABASE.keys()))
        random_info = " *(randomly chosen 🎲)*"
    else:
        chosen_category = category.lower()
        random_info = ""
        if chosen_category not in WORDS_DATABASE:
            categories_dispo = ", ".join(WORDS_DATABASE.keys())
            await interaction.response.send_message(
                f"❌ Unknown category. Available: `{categories_dispo}`", 
                ephemeral=True
            )
            return

    view = GameSetupView(category=chosen_category, nb_undercover=undercovers, nb_white=mr_whites)
    
    await interaction.response.send_message(
        f"Setting up your Undercover game!\n"
        f"📂 Category: `{chosen_category.capitalize()}`{random_info}\n"
        f"⚙️ Settings: {undercovers} Undercover(s) and {mr_whites} Mr. White(s).\n"
        f"👇 Select the players:",
        view=view,
        ephemeral=True
    )

bot.run(os.getenv("DISCORD_TOKEN"))