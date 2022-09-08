from classes.ranking_class import GlobalRanking, GuildRanking
from utils.kv_namespaces import *

cached_global_record = {}
# 将来的には可変に？
RANKING_WORD_COUNT = 10


async def get_guild_ranking(guild_id: int) -> GuildRanking:
    data = await guild_ranking_namespace.read(str(guild_id))
    return GuildRanking(json_data=data) if data else GuildRanking(word_count=RANKING_WORD_COUNT, guild_id=guild_id)


async def add_guild_ranking_records(game) -> None:
    guild_ranking = await get_guild_ranking(game.guild_id)
    guild_ranking.add_records(game.players_average_time)
    await guild_ranking_namespace.write({game.guild_id: guild_ranking.dict()})
    return


async def get_global_ranking() -> GlobalRanking:
    if cached_global_record:
        return GlobalRanking(word_count=RANKING_WORD_COUNT, competitors_record=cached_global_record)
    kv_keys = await global_ranking_namespace.list_keys()
    data = {}
    for user_id in kv_keys:
        data[int(user_id)] = float(await global_ranking_namespace.read(user_id))
    cached_global_record.update(data)
    return GlobalRanking(word_count=RANKING_WORD_COUNT, competitors_record=data)


async def add_global_ranking_records(user_records: dict) -> None:
    global_ranking_user_ids = await global_ranking_namespace.list_keys()
    for user_id in list(user_records):
        time = user_records[user_id]
        if str(user_id) in global_ranking_user_ids:
            # 過去の記録の方が早い場合は更新しない
            if float(await global_ranking_namespace.read(str(user_id))) < time:
                user_records.pop(user_id)
    await global_ranking_namespace.write(user_records)
    cached_global_record.update(user_records)
    return None
