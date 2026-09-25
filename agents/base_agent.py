# agents/base_agent.py
#
# Interface chuẩn mà MỌI agent (DFS, BFS, A*, Heuristic, hay thuật toán tự nghĩ ra)
# phải implement. Mỗi thành viên trong nhóm chỉ cần:
#   1. Tạo file mới trong agents/ (hoặc sửa file skeleton có sẵn)
#   2. Kế thừa BaseAgent
#   3. Implement choose_action()
#
# Không cần đụng vào core/ hay game/ - chỉ làm việc với observation trả về từ MinesweeperEnv.

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    name = "BaseAgent"

    @abstractmethod
    def choose_action(self, observation, env):
        """
        observation: ma trận rows x cols (list-of-list), giá trị:
            -1    = ô chưa đào (unknown)
            -2    = ô đã cắm cờ
            0..8  = số mìn lân cận (ô đã đào)

        env: instance của MinesweeperEnv, có thể dùng để:
            - env.rows, env.cols, env.mines : kích thước bàn chơi & tổng số mìn
            - env.valid_actions()           : list toạ độ (x, y) các ô chưa đào
            - env.board.grid[x][y]          : truy cập trực tiếp Tile nếu cần
              (lưu ý: KHÔNG được đọc tile.is_mine hay Board.board_grid - vì chúng chứa vị trí của bom, agent chỉ
              được phép dựa vào observation như một người chơi thật)

        Return: 1 action dạng tuple, ví dụ:
            ("reveal", 3, 4) - lật 1 ô ở vị trí (3, 4)
            ("flag", 0, 0) - cắm cờ ở ô vị trí (3, 4). Có thể gọi lại ở cùng tọa độ để toggle cờ
        """
        raise NotImplementedError
