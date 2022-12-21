from abc import ABC

import discord
from discord.commands import Option
from discord.ext import commands

from classes import button_classes
from classes.game_class import Game
from classes.ranking_class import *
from utils import games_manager, envs, rankings, aggregate_queue


class Bot(commands.Bot, ABC):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())


bot = Bot()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"/helpでヘルプ | {len(bot.guilds)}servers"))
    print("logged in")


@bot.slash_command(name="help")
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="タイピングBot", description="回答はひらがな、またはローマ字で入力してください。"
                                                        "\n**ランキングは10文字の問題を解くと対象になります。**"
                                                        "\n問題は寿司打のものを利用しています。",
                          color=discord.Color.green())
    embed.add_field(name="/ゲーム開始", value="ゲームを開始します。", inline=False)
    embed.add_field(name="/サーバーランキング",
                    value="サーバー内でのランキングを表示します。", inline=False)
    embed.add_field(name="/グローバルランキング",
                    value="全利用者中のランキングを表示します。", inline=False)
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="ゲーム開始", description="ランキングの対象は10文字です。")
async def game_start(
        ctx: discord.ApplicationContext,
        word_count: Option(str, "問題の文字数を選択", name="文字数", choices=[str(i) for i in range(2, 15)])  # noqa
):
    if games_manager.is_game_exists(channel_id=ctx.channel_id):
        await ctx.respond("進行中のゲームがあります。先にそちらを終了して下さい。")
        return
    word_count = int(word_count)
    game = Game(guild_id=ctx.guild_id,
                channel_id=ctx.channel_id, word_count=word_count)
    game.add_player(member_id=ctx.author.id)
    game.save()
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameJoinButton())
    view.add_item(button_classes.GameLeaveButton())
    view.add_item(button_classes.GameStartButton())
    view.add_item(button_classes.GameQuitButton())

    embed = discord.Embed(title="参加する人は参加ボタンを押して下さい。\n"
                                "**回答はひらがな、もしくはローマ字で入力してください。**\n"
                                "用意が出来たらスタートボタンでゲームを開始できます。\n\n"
                                "中止ボタンでゲームを中止出来ます。",
                          color=discord.Color.blue())
    embed.add_field(name="文字数", value=f"{word_count}文字")
    embed.add_field(name="参加者", value=ctx.author.display_name)
    await ctx.respond(embed=embed, view=view)
    await aggregate_queue.create_queue(ctx.channel_id)


@bot.slash_command(name="サーバーランキング", description="このサーバー内でのランキングを表示します。")
async def guild_ranking(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="このサーバーでの順位", color=discord.Color.green(),
                          description=f"読み込み中...")
    await ctx.interaction.response.send_message(embed=embed)
    ranking: GuildRanking = await rankings.get_guild_ranking(guild_id=ctx.guild.id)
    all_records: dict = ranking.get_all_records()
    embed = discord.Embed(title="このサーバーでの順位", color=discord.Color.green(),
                          description=f"文字数：{ranking.word_count}文字")
    for user_id in all_records:
        rank = list(all_records.keys()).index(user_id) + 1
        member = ctx.guild.get_member(user_id)
        embed.add_field(name=f"{rank}位 {member.display_name}#{member.discriminator}",
                        value=f"{all_records[user_id]}秒", inline=False)
    await ctx.interaction.edit_original_response(embed=embed)


@bot.slash_command(name="全体ランキング", description="全サーバー総合でのランキングを表示します。")
async def global_ranking(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="全サーバーでの順位", color=discord.Color.green(),
                          description=f"読み込み中...")
    await ctx.interaction.response.send_message(embed=embed)
    ranking: GlobalRanking = await rankings.get_global_ranking()
    all_records = ranking.get_all_records()
    embed = discord.Embed(title="全サーバーでの順位", color=discord.Color.green(),
                          description=f"文字数：{ranking.word_count}文字")
    for user_id in all_records:
        rank = list(all_records.keys()).index(user_id) + 1
        user = bot.get_user(int(user_id))
        try:
            user = await bot.fetch_user(int(user_id)) if user is None else user
        except discord.NotFound:
            continue
        embed.add_field(name=f"{rank}位 {user.name}#{user.discriminator if user else ''}",
                        value=f"{all_records[user_id]}秒", inline=False)
    await ctx.interaction.edit_original_response(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if not games_manager.is_game_exists(channel_id=message.channel.id):
        return
    if message.author.bot:
        return  # ボットは無視
    game = games_manager.get_game(channel_id=message.channel.id)
    if game is None or message.author.id not in game.player_list or not game.is_answering(message.author.id):
        return
    await aggregate_queue.queues[message.channel.id].put(message)

try:
    bot.run(envs.TOKEN)
finally:
    pass
