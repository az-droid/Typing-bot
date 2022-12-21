import asyncio
import discord
from discord.ui import Button

from utils import games_manager
from classes.game_class import Game


class GameJoinButton(Button):
    def __init__(self):
        super().__init__(
            label="参加",
            style=discord.enums.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: Game = games_manager.get_game(channel_id)
        if game is None:
            return
        if user.id in game.player_list:
            return
        game.add_player(member_id=user.id)
        game.save()
        embed = interaction.message.embeds[0]
        players_field = embed.fields[1]
        field_value = f"{players_field.value}\n{user.display_name}"
        embed.set_field_at(index=1, name="参加者", value=field_value)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"ゲームに参加しました！", ephemeral=True)


class GameLeaveButton(Button):
    def __init__(self):
        super().__init__(
            label="抜ける",
            style=discord.enums.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: Game = games_manager.get_game(channel_id)
        if game is None:
            return
        if user.id not in game.player_list:
            return
        if len(game.player_list) == 1:
            games_manager.remove_game(game)
            await interaction.response.send_message(f"ゲームを中止しました。", ephemeral=False)
            return
        game.remove_player(user.id)
        game.save()
        embed = interaction.message.embeds[0]
        players_field = embed.fields[1]
        players_list = players_field.value.splitlines()
        players_list.remove(user.display_name)
        field_value = "\n".join(players_list)
        embed.set_field_at(index=1, name="参加者", value=field_value)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"ゲームから抜けました。", ephemeral=True)


class GameStartButton(Button):
    def __init__(self):
        super().__init__(
            label="ゲーム開始",
            style=discord.enums.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: Game = games_manager.get_game(channel_id)
        if game is None:
            return
        view = discord.ui.View(timeout=None)
        view.add_item(NextQuestionButton())
        view.add_item(GameQuitButton())
        await interaction.response.send_message(f"5秒後にゲームを開始します！", ephemeral=False)
        for i in (4, 3, 2, 1):
            await asyncio.sleep(1)
            await interaction.edit_original_response(content=f"{i}秒後にゲームを開始します！")

        for user_id in game.player_list:
            game.start_answering(user_id)
        question = game.get_next_question()
        game.save()
        embed = discord.Embed(title=f"問題1：{question}",
                              color=discord.Color.blurple())
        await interaction.channel.send(embed=embed, view=view)
        await interaction.message.delete()


class GameQuitButton(Button):
    def __init__(self):
        super().__init__(
            label="中止",
            style=discord.enums.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: Game = games_manager.get_game(channel_id)
        if game is None:
            return
        games_manager.remove_game(game)
        await interaction.response.send_message(f"ゲームを中止しました。", ephemeral=False)


class NextQuestionButton(Button):
    def __init__(self):
        super().__init__(
            label="次の問題へ",
            style=discord.enums.ButtonStyle.blurple
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: Game = games_manager.get_game(channel_id)
        if game is None:
            return
        question = game.get_next_question()
        for user_id in game.player_list:
            game.start_answering(user_id)
        question_number = game.question_index + 1
        embed = discord.Embed(title=f"問題{question_number}：{question}", color=discord.Color.blurple())
        game.save()
        view = discord.ui.View(timeout=None)
        view.add_item(NextQuestionButton())
        view.add_item(GameQuitButton())
        await interaction.channel.send(embed=embed, view=view)
