# agents/random_agent.py
#
# Agent baseline đơn giản nhất: chọn ngẫu nhiên 1 ô chưa đào để đào.
# Đây là agent DUY NHẤT đã hoạt động hoàn chỉnh ngay từ đầu - dùng để:
#   1. Test framework (env, runner) hoạt động đúng trước khi ai đó viết thuật toán thật.
#   2. Làm baseline so sánh: nếu DFS/BFS/A*/Heuristic của bạn thắng không cao hơn
#      random đáng kể thì chắc là thuật toán có vấn đề.

import random
from agents.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    name = "RandomAgent"

    def choose_action(self, observation, env):
        x, y = random.choice(env.valid_actions())
        return ("reveal", x, y)
