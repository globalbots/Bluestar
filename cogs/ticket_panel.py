import asyncio
import discord
from discord import ui
from discord.ext import commands

import database

EMOJI_HEADER = discord.PartialEmoji(name="name", id=1547248087913734255)
EMOJI_OWNER = discord.PartialEmoji(name="name", id=1547267746549465178)
EMOJI_CRIMINAL = discord.PartialEmoji(name="name", id=1548689203154653274)
EMOJI_SUPPORT = discord.PartialEmoji(name="name", id=1548689650787287150, animated=True)
EMOJI_BUG = discord.PartialEmoji(name="name", id=1548689485154226226)
EMOJI_REWARD = discord.PartialEmoji(name="name", id=1548689528254894223)
EMOJI_STAFF = discord.PartialEmoji(name="name", id=1548689281223229490)
EMOJI_MANAGER = discord.PartialEmoji(name="name", id=1548689327872151582)
EMOJI_WELCOME = discord.PartialEmoji(name="name", id=1547248247540555936)

CATEGORY_MAP = {
    "option_1": "Owner",
    "option_2": "Criminal",
    "option_3": "Support",
    "option_4": "Bug Report",
    "option_5": "Claim Your Reward",
    "option_6": "Staff Application",
    "option_7": "Manager Application",
}

CATEGORY_CHANNEL_IDS = {
    "Owner": None,
    "Criminal": None,
    "Support": None,
    "Bug Report": None,
    "Claim Your Reward": None,
    "Staff Application": None,
    "Manager Application": None,
}

class TicketSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Owner", value="option_1", emoji=EMOJI_OWNER),
            discord.SelectOption(label="Criminal", value="option_2", emoji=EMOJI_CRIMINAL),
            discord.SelectOption(label="Support", value="option_3", emoji=EMOJI_SUPPORT),
            discord.SelectOption(label="Bug Report", value="option_4", emoji=EMOJI_BUG),
            discord.SelectOption(label="Claim Your Reward", value="option_5", emoji=EMOJI_REWARD),
            discord.SelectOption(label="Staff Application", value="option_6", emoji=EMOJI_STAFF),
            discord.SelectOption(label="Manager Application", value="option_7", emoji=EMOJI_MANAGER),
        ]
        super().__init__(
            custom_id="select_option",
            placeholder="Choose an option",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        category = CATEGORY_MAP[self.values[0]]
        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        role_ids = await database.get_category_roles(guild.id, category)
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        category_id = CATEGORY_CHANNEL_IDS.get(category)
        category_channel = guild.get_channel(category_id) if category_id else None

        if category_id and category_channel is None:
            await interaction.followup.send(
                f"Δεν βρέθηκε Discord category με id `{category_id}` για **{category}**. ",
                ephemeral=True,
            )

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category_channel,
            overwrites=overwrites,
        )

        await database.create_ticket(ticket_channel.id, guild.id, interaction.user.id, category)

        view = TicketChannelView(interaction.user)
        await ticket_channel.send(view=view)

        await interaction.followup.send(
            f"Το ticket σου δημιουργήθηκε: {ticket_channel.mention}", ephemeral=True
        )


class TicketPanelView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = ui.Container()

        container.add_item(
            ui.Section(
                ui.TextDisplay(f"## **{EMOJI_HEADER}__Bluestar Arena Ticket Center __**"),
                accessory=ui.Thumbnail(url="https://i.imgur.com/LLMFb9t.png"),
            )
        )
        container.add_item(ui.Separator(divider=True, spacing=discord.SeparatorSpacing.small))
        container.add_item(
            ui.TextDisplay(
                f"{EMOJI_HEADER} **Για την καλύτερη εξυπηρέτηση σας επιλέξτε το ticket "
                f"απο το dropdown category που σας ταιριάζει και επικοινωνήστε μαζί μας.**"
            )
        )
        container.add_item(ui.Separator(divider=True, spacing=discord.SeparatorSpacing.large))

        action_row = ui.ActionRow()
        action_row.add_item(TicketSelect())
        container.add_item(action_row)

        container.add_item(ui.Separator(divider=True, spacing=discord.SeparatorSpacing.small))

        self.add_item(container)

class CloseButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            custom_id="btn_action",
        )

    async def callback(self, interaction: discord.Interaction):
        ticket = await database.get_ticket(interaction.channel_id)
        if ticket is None:
            await interaction.response.send_message(
                "Αυτό το κανάλι δεν είναι αποθυκευμένο ως ticket.", ephemeral=True
            )
            return

        await interaction.response.send_message("Το ticket κλείνει σε 5 δευτερόλεπτα...")
        await database.delete_ticket(interaction.channel_id)
        await asyncio.sleep(5)
        await interaction.channel.delete()


class TicketChannelView(ui.LayoutView):
    def __init__(self, user: discord.abc.User):
        super().__init__(timeout=None)

        container = ui.Container()

        container.add_item(
            ui.Section(
                ui.TextDisplay(
                    f"### {EMOJI_WELCOME} __Καλώς ήρθες στο ticket σου {user.mention}__\n"
                    f"> Πές μας τι χρειάζεσαι και σύντομα θα σε εξυπηρετήσει ένα μέλος της ομάδας μας."
                ),
                accessory=ui.Thumbnail(url="https://i.imgur.com/LLMFb9t.png"),
            )
        )
        container.add_item(ui.Separator(divider=True, spacing=discord.SeparatorSpacing.small))

        action_row = ui.ActionRow()
        action_row.add_item(CloseButton())
        container.add_item(action_row)

        self.add_item(container)


class TicketPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="panel", description="Στείλε το ticket panel στο κανάλι")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def panel(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=TicketPanelView())


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketPanelCog(bot))
