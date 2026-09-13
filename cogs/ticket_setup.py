import discord
from discord import app_commands, ui
from discord.ext import commands

import database

CATEGORIES = [
    "Owner",
    "Criminal",
    "Support",
    "Bug Report",
    "Claim Your Reward",
    "Staff Application",
    "Manager Application",
]


class CategorySelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=c, value=c) for c in CATEGORIES]
        super().__init__(placeholder="Επίλεξε category", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        view = RoleSelectView(interaction.guild_id, category)
        await interaction.response.edit_message(
            content=f"Category: **{category}**\nEπίλεξε ποιος/ποιοι ρόλοι θα βλέπουν τα tickets ",
            view=view,
        )


class CategorySelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(CategorySelect())


class RoleSelectMenu(ui.RoleSelect):
    def __init__(self, guild_id: int, category: str):
        super().__init__(placeholder="Επίλεξε role", min_values=1, max_values=10)
        self.guild_id = guild_id
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        await database.set_category_roles(
            self.guild_id, self.category, [role.id for role in self.values]
        )
        role_mentions = ", ".join(role.mention for role in self.values)
        await interaction.response.edit_message(
            content=f"Το category **{self.category}** θα βλέπεται από: {role_mentions}",
            view=None,
        )


class RoleSelectView(ui.View):
    def __init__(self, guild_id: int, category: str):
        super().__init__(timeout=120)
        self.add_item(RoleSelectMenu(guild_id, category))


class TicketSetupGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="setview", description="Ρυθμίσεις εμφάνισης tickets")

    @app_commands.command(name="ticket", description="Όρισε ποιοι ρόλοι βλέπουν κάθε category ticket")
    async def ticket(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "Μόνο ο owner του server μπορεί να χρησιμοποιήσει την εντολή.",
                ephemeral=True,
            )
            return

        view = CategorySelectView()
        await interaction.response.send_message(
            "Επίλεξε για ποιο category θέλεις να ορίσεις roles:",
            view=view,
            ephemeral=True,
        )


class TicketSetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    bot.tree.add_command(TicketSetupGroup())
    await bot.add_cog(TicketSetupCog(bot))
