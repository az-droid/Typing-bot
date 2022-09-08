import asyncio
from typing import Tuple

import discord

from classes import button_classes
from utils import games_manager

queued_messages = {}


def create_queue(game):
    queued_messages[game.channel_id] = []


async def append(message: discord.Message):
    queued_messages[message.channel.id].append(message)
    if len(queued_messages[message.channel.id]) > 1:
        return
    game = games_manager.get_game(message.channel.id)
    while len(queued_messages[message.channel.id]) > 0:
        message: discord.Message = queued_messages[game.channel_id].pop(-1)
        # 答え合わせ
        try:
            is_correct, is_last_question = await check_answer(message, game)
        except ValueError("player status is not 'answering'"):
            continue
        # 正解の場合の処理
        if not is_correct:
            continue
        # 全プレイヤーが回答済み(=集計キューが空)の場合
        if game.is_all_player_answered():
            # 最後の問題の場合は全体の集計結果を表示
            if is_last_question:
                await send_all_aggregated_result(message, game)
                await games_manager.end_game(channel_id=message.channel.id)
            # そうでない場合は次の問題に移行
            else:
                await move_to_next_question(message, game)


async def check_answer(message: discord.Message, game) -> Tuple[bool, bool]:
    embeds = []
    if not game.is_answering(user_id=message.author.id):
        raise ValueError("player status is not 'answering'")
    is_correct, elapsed_time, user_input = game.submit_answer(msg_created_at=message.created_at.timestamp(),
                                                              user_id=message.author.id, user_input=message.content)
    game.save()
    is_last_question = False
    if not is_correct:
        embed = discord.Embed(title="不正解です。", description=f"入力：{user_input}", color=discord.Color.red())
        embeds.append(embed)
    else:
        embed = discord.Embed(title="正解です！",
                              description=f"回答時間：{elapsed_time}秒", color=discord.Color.green())
        embeds.append(embed)

        is_last_question = game.question_index == 9
        if is_last_question:
            average_time, not_answered_question_count = game.aggregate_user_result(user_id=message.author.id)
            embed = discord.Embed(title=f"あなたの平均タイムは{average_time:.03f}秒です。",
                                  description=f"未回答の問題：{not_answered_question_count}問",
                                  color=discord.Color.greyple())
            embeds.append(embed)
    await message.reply(embeds=embeds)
    return is_correct, is_last_question


async def move_to_next_question(message: discord.Message, game):
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameQuitButton())
    embed = discord.Embed(title="全員が答え合わせを終了しました。\n3秒後に次の問題に進みます。", description="中止ボタンでゲームを中止出来ます。")
    next_question_message = await message.channel.send(embed=embed, view=view)
    await asyncio.sleep(1)
    for i in (2, 1):
        embed = discord.Embed(title=f"全員が答え合わせを終了しました。\n{i}秒後に次の問題に進みます。", description="中止ボタンでゲームを中止出来ます。")
        await asyncio.sleep(1)
    await next_question_message.edit(embed=embed, view=view)
    question = game.get_next_question()
    question_number = game.question_index + 1
    embed = discord.Embed(title=f"問題{question_number}：{question}", color=discord.Color.blurple())
    for user_id in game.player_list:
        game.start_answering(user_id=user_id)
    game.save()
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.NextQuestionButton())
    view.add_item(button_classes.GameQuitButton())
    await next_question_message.edit(embed=embed, view=view)


async def send_all_aggregated_result(message: discord.Message, game):
    embed = discord.Embed(title="全員の平均タイム", color=discord.Color.orange())
    players_sorted_time, players_not_answered_count = game.aggregate_all_result()
    ranking = 0
    for t in players_sorted_time:
        user_id = t[0]
        average_time = t[1]
        ranking += 1
        member = message.guild.get_member(user_id)
        embed.add_field(name=f"{ranking}位 {member.name}",
                        value=f"{average_time:.03f}秒\n未回答の問題：{players_not_answered_count[user_id]}問",
                        inline=False)
    await message.channel.send(embed=embed)
