import datetime
import json
import os


class ShortTermMemory:
    def __init__(self, memory_file=None):
        self.memory_file = memory_file

        self._current_time = None
        self._current_place = None
        self._current_weather = None
        self._current_temperature = None
        self._name = None
        self._family_name = None
        self._given_name = None
        self._age = None
        self._gender = None
        self._profession = None
        self._daily_plan = []
        self._daily_schedule = []
        self._daily_logs = []

        # 如果文件存在，读取文件
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                st = f.read()
            st = json.loads(st)
            # self.current_time = datetime.datetime.strptime(
            #     st["当前时间"], "%B %d, %Y, %H:%M:%S"
            # )
            # self._current_place = st["当前地点"]
            # self._current_weather = st["当前天气"]
            # self._current_temperature = st["当前温度"]
            # self._name = st["姓名"]
            # self._family_name = st["姓"]
            # self._given_name = st["名"]
            # self._age = st["年龄"]
            # self._gender = st["性别"]
            # self._profession = st["职业"]
            # self._daily_plan = st["今日计划"]
            # self._daily_schedule = st["今日日程"]
            self._daily_logs = st["今日日志"]

    def shot_memory(self):
        st = {}
        st["今日日志"] = self._daily_logs
        return st

    def remember(self):
        st = {}
        # st["当前时间"] = self._current_time
        # st["当前地点"] = self._current_place
        # st["当前天气"] = self._current_weather
        # st["当前温度"] = self._current_temperature
        # st["姓名"] = self._name
        # st["姓"] = self._family_name
        # st["名"] = self._given_name
        # st["年龄"] = self._age
        # st["性别"] = self._gender
        # st["职业"] = self._profession
        # st["今日计划"] = self._daily_plan
        # st["今日日程"] = self._daily_schedule
        st["今日日志"] = self._daily_logs

        with open(self.memory_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(st, ensure_ascii=False, indent=4))

    def recall(self):
        pass

    @property
    def current_time(self):
        return self._current_time

    @current_time.setter
    def current_time(self, value):
        self._current_time = value

    @property
    def current_place(self):
        return self._current_place

    @current_place.setter
    def current_place(self, value):
        self._current_place = value

    @property
    def current_weather(self):
        return self._current_weather

    @current_weather.setter
    def current_weather(self, value):
        self._current_weather = value

    @property
    def current_temperature(self):
        return self._current_temperature

    @current_temperature.setter
    def current_temperature(self, value):
        self._current_temperature = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def family_name(self):
        return self._family_name

    @family_name.setter
    def family_name(self, value):
        self._family_name = value

    @property
    def given_name(self):
        return self._given_name

    @given_name.setter
    def given_name(self, value):
        self._given_name = value

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        self._age = value

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, value):
        self._gender = value

    @property
    def profession(self):
        return self._profession

    @profession.setter
    def profession(self, value):
        self._profession = value

    @property
    def daily_plan(self):
        return self._daily_plan

    @daily_plan.setter
    def daily_plan(self, value):
        self._daily_plan = value

    @property
    def daily_schedule(self):
        return self._daily_schedule

    @daily_schedule.setter
    def daily_schedule(self, value):
        self._daily_schedule = value

    @property
    def daily_logs(self):
        return self._daily_logs

    @daily_logs.setter
    def daily_logs(self, value):
        self._daily_logs = value
