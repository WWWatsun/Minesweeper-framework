import argparse
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import MinesweeperEnv
from core.board import GameState
from agents.random_agent import RandomAgent
#from agents.dfs_agent import DFSAgent
#from agents.bfs_agent import BFSAgent
#from agents.astar_agent import AStarAgent
#from agents.heuristic_agent import HeuristicAgent

AGENTS = {
    "random": RandomAgent,
    #"dfs": DFSAgent,
    #"bfs": BFSAgent,
    #"astar": AStarAgent,
    #"heuristic": HeuristicAgent,
}

def run_episode(env, agent, max_steps=10000):
    env.reset()
    obs = env._get_obs()
    steps = 0
    while not env.done and steps < max_steps:
        action = agent.choose_action(obs, env)
        obs, reward, done, info = env.step(action)
        steps += 1
    return env.board.state, steps

# Hiển thị kết quả lên terminal, không render
def run_headless(agent_name, episodes, rows, cols, mines):
    agent = AGENTS[agent_name]()
    env = MinesweeperEnv(rows=rows, cols=cols, mines=mines)

    wins = 0
    total_steps = 0
    start = time.time()
    for _ in range(episodes):
        state, steps = run_episode(env, agent)
        total_steps += steps
        if state == GameState.WON:
            wins += 1
    elapsed = time.time() - start

    print(f"Agent:        {agent.name}")
    print(f"Bàn chơi:     {rows}x{cols}, mines={mines}")
    print(f"Số ván:       {episodes}")
    print(f"Tỉ lệ thắng:  {wins}/{episodes} ({100 * wins / episodes:.1f}%)")
    print(f"Số bước TB:   {total_steps / episodes:.1f} / ván")
    print(f"Thời gian:    {elapsed:.2f}s")
    env.render()

# Render game board để xem các bước trong thời gian thực.
def run_with_render(agent_name, rows, cols, mines):
    import pygame
    from game_settings import TILESIZE, BGCOLOUR, TITLE
    from game.sprites import BoardView

    agent = AGENTS[agent_name]()
    env = MinesweeperEnv(rows=rows, cols=cols, mines=mines)
    obs = env.reset()

    pygame.init()
    pygame.display.set_caption(f"{TITLE} - Agent: {agent.name}")
    screen = pygame.display.set_mode((cols * TILESIZE, rows * TILESIZE))
    clock = pygame.time.Clock()
    view = BoardView(env.board)

    running = True
    while running:
        # chậm khi agent đang chơi, nhanh khi đã xong để click phản hồi ngay
        clock.tick(30 if env.done else 1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and env.done:
                running = False          # click sau khi ván kết thúc -> đóng

        if not env.done and running:
            action = agent.choose_action(obs, env)
            obs, reward, done, info = env.step(action)
            if done and info.get("result") == "loss":
                view.reveal_all_on_loss()

        screen.fill(BGCOLOUR)
        view.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy agent Minesweeper solver.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="random")
    parser.add_argument("--episodes", type=int, default=50, help="Số ván (chỉ áp dụng khi chạy headless)")
    parser.add_argument("--rows", type=int, default=15)
    parser.add_argument("--cols", type=int, default=15)
    parser.add_argument("--mines", type=int, default=20)
    parser.add_argument("--render", action="store_true", help="Hiển thị bằng pygame thay vì chạy headless")
    args = parser.parse_args()

    if args.render:
        run_with_render(args.agent, args.rows, args.cols, args.mines)
    else:
        run_headless(args.agent, args.episodes, args.rows, args.cols, args.mines)

