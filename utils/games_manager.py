from classes.game_class import Game
from utils import rankings

games = {}


def get_game(channel_id: int) -> Game:
    return games.get(channel_id)


def save_game(game: Game):
    channel_id = game.channel_id
    games[channel_id] = game


def remove_game(game: Game):
    channel_id = game.channel_id
    games.pop(channel_id, None)


def is_game_exists(channel_id: int):
    if channel_id in games:
        return True
    else:
        return False


async def end_game(channel_id: int):
    game: Game = games.pop(channel_id)
    if not game.is_ranking_active:
        return
    await rankings.add_guild_ranking_records(game)
    await rankings.add_global_ranking_records(game.players_average_time)
    return
