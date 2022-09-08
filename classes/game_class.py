import json
import random
import re
import time
from typing import Tuple

import numpy as numpy
from google_input.filter_rule import FilterRuleTable
from google_input.ime import GoogleInputIME

from utils import aggregate_queue
from utils import games_manager
from utils.rankings import RANKING_WORD_COUNT

with open('files/sushida.json', encoding='utf-8') as f:
    sushida_dict = json.load(f)

table = FilterRuleTable.from_file("files/google_ime_default_roman_table.txt")
ime = GoogleInputIME(table)
alphabet_regex = re.compile('[ -~]+')


class Game:
    def __init__(self, guild_id: int, channel_id: int, word_count: int):
        self.competitors_time = {}
        self.players_average_time = {}
        self.competitors_status = {}
        self.start_time = int()
        self.player_list = []
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.question_list = generate_question_list(word_count)
        self.question_index = -1
        self.word_count = word_count
        self.is_ranking_active = True if word_count == RANKING_WORD_COUNT else False
        aggregate_queue.create_queue(self)

    def save(self):
        games_manager.save_game(self)

    def add_player(self, member_id: int):
        self.player_list.append(member_id)
        self.competitors_time[member_id] = []

    def remove_player(self, member_id: int):
        self.player_list.remove(member_id)
        del self.competitors_time[member_id]
        del self.competitors_status[member_id]

    def get_next_question(self):
        self.question_index += 1
        return self.question_list[self.question_index][1]

    def start_answering(self, user_id: int):
        self.start_time = time.time()
        self.competitors_status[user_id] = 'answering'

    def is_answering(self, user_id: int):
        return self.competitors_status[user_id] == 'answering'

    def is_all_player_answered(self):
        for status in self.competitors_status.values():
            if status != 'answered':
                return False
        return True

    def submit_answer(self, msg_created_at: float, user_id: int, user_input: str) -> Tuple[bool, float, str]:
        """
        is_correctは正解の場合はTrue、不正解の場合はFalse
        Args:
            msg_created_at: float
            user_id: int
            user_input: str

        Returns:
            is_correct: bool
            elapsed_time: int
            user_input: str
        """
        is_answer_right, user_input = _check_answer(self, user_input)
        if is_answer_right:
            self.competitors_status[user_id] = 'answered'
            elapsed_time = msg_created_at - self.start_time
            self.competitors_time[user_id].append(elapsed_time)
            return True, elapsed_time, user_input
        return False, 0, user_input

    def aggregate_user_result(self, user_id: int):
        """
        回答したユーザーのみ集計する
        Args:
            user_id:

        Returns:
            average_time: float
        """
        average = numpy.average(self.competitors_time[user_id])
        not_answered_question_count = 10 - len(self.competitors_time[user_id])
        if not_answered_question_count == 0:
            self.players_average_time[user_id] = average
        return average, not_answered_question_count

    def aggregate_all_result(self):
        """
        全員が回答したら、結果を集計する
        Returns:
            players_sorted_time: dict
            players_not_answered_question_count: dict
        """
        players_average_time = {}
        players_not_answered_question_count = {}
        for user_id in self.player_list:
            average = numpy.average(self.competitors_time[user_id])
            players_average_time[user_id] = average
            players_not_answered_question_count[user_id] = 10 - len(self.competitors_time[user_id])
            if players_not_answered_question_count[user_id] == 0:
                players_average_time[user_id] = average
        players_sorted_time = sorted(players_average_time.items(), key=lambda x: x[1])
        return players_sorted_time, players_not_answered_question_count


def generate_question_list(word_count: int):
    question_lists = random.sample(sushida_dict[str(word_count)], 10)
    return question_lists


def _check_answer(game: Game, user_input: str) -> Tuple[bool, str]:
    if alphabet_regex.fullmatch(user_input):
        user_input = rome_to_hiragana(user_input)
    user_input = user_input.replace('!', '！').replace('?', '？')
    question = game.question_list[game.question_index]
    right_answer = question[0]
    return right_answer == user_input, user_input


def rome_to_hiragana(input_string):
    output = []
    for c in input_string:
        results = ime.input(c)
        output.append("".join(r.output_rule.output for r in results if r.output_rule))
    return "".join(output)
