import json


class GuildRanking:
    def __init__(self, guild_id: int = None,
                 word_count: int = None,
                 json_data: dict = None):
        if json_data is not None:
            self.guild_id = json_data["guild_id"]
            self.word_count = json_data["word_count"]
            self.competitors_records = {}
            for user_id in json_data["competitors_records"]:
                self.competitors_records[int(user_id)] = json_data["competitors_records"][user_id]
        else:
            if None in (guild_id, word_count):
                raise ValueError("guild_id and word_count can't be None if json_data is not passed.")
            self.guild_id = guild_id
            self.word_count = word_count
            self.competitors_records = {}

    def add_records(self, user_records):
        for user_id in list(user_records):
            time = user_records[user_id]
            if user_id in self.competitors_records:
                # 過去の記録の方が早い場合は更新しない
                if float(self.competitors_records[user_id]) < time:
                    user_records.pop(user_id)
        self.competitors_records.update(user_records)

    def get_all_records(self, sort_by_time: bool = True):
        records = {}
        if sort_by_time:
            sorted_tuple = sorted(self.competitors_records.items(), key=lambda x: x[1])
            i: tuple
            for i in sorted_tuple:
                user_id = i[0]
                time = self.competitors_records[user_id]
                records[user_id] = time
        else:
            for user_id in self.competitors_records:
                records[user_id] = self.competitors_records[user_id]
        return records

    def is_user_in_ranking(self, user_id: int):
        return user_id in self.competitors_records

    def get_user_record(self, user_id: int):
        return self.competitors_records.get(user_id)

    def dict(self):
        return {
            "guild_id": self.guild_id,
            "word_count": self.word_count,
            "competitors_records": self.competitors_records
        }


class GlobalRanking:
    def __init__(self, word_count: int, competitors_record: dict):
        self.word_count = word_count
        self.competitors_records = {}
        for user_id in competitors_record:
            self.competitors_records[int(user_id)] = competitors_record[user_id]

    def is_user_in_ranking(self, user_id: int):
        return int(user_id) in self.competitors_records

    def get_user_record(self, user_id: int):
        return self.competitors_records.get(user_id)

    def get_all_records(self, sort_by_time: bool = True):
        records = {}
        if sort_by_time:
            sorted_tuple = sorted(self.competitors_records.items(), key=lambda x: x[1])
            i: tuple
            for i in sorted_tuple:
                user_id = i[0]
                time = self.competitors_records[user_id]
                records[user_id] = time
        else:
            for user_id in self.competitors_records:
                records[user_id] = self.competitors_records[user_id]
        return records
