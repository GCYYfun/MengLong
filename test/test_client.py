import os
import sys
import unittest

# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.model_interface import Model
from mlong.model_interface.utils import user, assistant, system


class ClientTests(unittest.TestCase):
    def test_client(self):
        client = Model()  # configs={"aws": {}}
        res = client.chat(
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            [user("hello")],
        )
        self.assertIsInstance(res.choices[0].message.content, str)

    def test_other(self):
        client = Model()
        res = client.chat(
            "us.amazon.nova-pro-v1:0",
            [user("hello")],
        )
        self.assertIsInstance(res.choices[0].message.content, str)

    # def test_both(self):
    #     client = Model()
    #     res = client.chat(
    #         "gpt-4",
    #         [user("hello")],
    #     )
    #     self.assertIsInstance(res.choices[0].message.content, str)
    #     res = client.chat(
    #         "us.amazon.nova-pro-v1:0",
    #         [user("hello")],
    #     )
    #     self.assertIsInstance(res.choices[0].message.content, str)


if __name__ == "__main__":
    unittest.main()
