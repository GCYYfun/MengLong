import os
import re

import yaml


class WorkingMemory:
    def __init__(self, memory_file=None):

        self.long_term_memory = None
        self.buffer = {}
        if memory_file is not None:
            self.memory_file = memory_file
            if os.path.exists(memory_file):
                print("Loading memory file...")
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.buffer = yaml.safe_load(f)
            else:
                print("Memory file does not exist. Init with empty buffer.")
                # 创建file 包括目录
                os.makedirs(os.path.dirname(memory_file), exist_ok=True)
                with open(memory_file, "w", encoding="utf-8") as f:
                    yaml.dump({"daily_logs": []}, f)
                self.buffer = {"daily_logs": []}
        else:
            print("No memory file provided.")
            self.buffer = {"daily_logs": []}

    @property
    def daily_logs(self):
        return self.buffer["daily_logs"]

    def central_executive(self, info):
        # save
        # save and query
        if not isinstance(info, dict):
            raise ValueError("Info must be a dictionary.")
        if "episode" in info:
            self.buffer["daily_logs"].append(info["episode"])
            self._update_memory_file()

    def phonological_loop(self, text):
        processed = {
            "words": len(re.findall(r"\w+", text)),
            "phonemes": self._count_phonemes(text),
            "type": "verbal",
        }
        return self.episodic_buffer(processed)

    def visuospatial_sketchpad(self, image):
        processed = {
            "shapes": self._detect_shapes(image),
            "colors": self._extract_colors(image),
            "type": "visual",
        }
        return self.episodic_buffer(processed)

    def episodic_buffer(self, info):
        if self.long_term_memory:
            info["related_memory"] = self.retrieve_long_term_memory(info)
        return self._normalize_memory(info)

    def retrieve_long_term_memory(self, info):
        pass

    def reset(self):
        self.buffer = {"daily_logs": []}

    def _update_memory_file(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            yaml.dump(self.buffer, f)
        # 这里可以实现更复杂的持久化逻辑，例如使用数据库等


# {
#     "事件内容": "记录具体发生的事件或活动的细节",
#     "时间地点": "事件发生的时间和地点信息",
#     "关联人物": "涉及的人物及其互动",
#     "情感体验": "事件伴随的情绪或感受",
#     "事件结果": "事件的结果或影响",
#     "动作与行为": "个人或他人的具体行为",
#     "自传体属性": "与‘自我’的关联性",
# }
