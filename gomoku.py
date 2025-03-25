import pygame
import sys
import requests
import re

from tkinter import messagebox, Tk
from config import MODEL_URL, AUTHORIZATION

# 初始化Pygame
pygame.init()

# 常量定义
BOARD_SIZE = 15
CELL_SIZE = 40
MARGIN = 20
WINDOW_SIZE = (BOARD_SIZE-1) * CELL_SIZE + MARGIN * 2
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)

# 初始化窗口
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption('五子棋')

# 棋盘数据
board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
player_turn = True  # True表示玩家回合，False表示电脑回合
selected_x, selected_y = BOARD_SIZE // 2, BOARD_SIZE // 2

def draw_board():
    screen.fill(WHITE)
    for i in range(BOARD_SIZE):
        pygame.draw.line(screen, BLACK, (MARGIN, MARGIN + i * CELL_SIZE), (WINDOW_SIZE - MARGIN, MARGIN + i * CELL_SIZE))
        pygame.draw.line(screen, BLACK, (MARGIN + i * CELL_SIZE, MARGIN), (MARGIN + i * CELL_SIZE, WINDOW_SIZE - MARGIN))
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] == 1:
                pygame.draw.circle(screen, BLACK, (MARGIN + x * CELL_SIZE, MARGIN + y * CELL_SIZE), CELL_SIZE // 2 - 2)
            elif board[y][x] == 2:
                pygame.draw.circle(screen, GRAY, (MARGIN + x * CELL_SIZE, MARGIN + y * CELL_SIZE), CELL_SIZE // 2 - 2)
    pygame.draw.rect(screen, GRAY, (MARGIN + selected_x * CELL_SIZE - CELL_SIZE // 2, MARGIN + selected_y * CELL_SIZE - CELL_SIZE // 2, CELL_SIZE, CELL_SIZE), 2)

# def show_message(message):
#     pygame.quit()  # 先退出 Pygame
#     root = Tk()
#     root.withdraw()  # 隐藏主窗口
#     messagebox.showinfo("游戏结束", message)
#     root.destroy()  # 销毁主窗口
#     sys.exit()

def show_message(message):
    font = pygame.font.Font(None, 36)
    text = font.render(message, True, (255, 0, 0))
    text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    screen.fill(WHITE)
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.wait(5000)  # 显示 3 秒后退出
    pygame.quit()
    sys.exit()

def check_win(board):
    # 计算当前棋盘上的棋子数量
    move_count = sum(sum(1 for cell in row if cell != 0) for row in board)
    print(f"move_count: {move_count}")  # 添加调试信息
    
    # 如果棋子数量少于9，不检查胜利条件
    if move_count < 9:
        return -1

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if x + 4 < BOARD_SIZE and all(board[y][x + i] == 1 for i in range(5)):
                print(f"Player 1 wins horizontally at ({x}, {y})")
                return 1
            if y + 4 < BOARD_SIZE and all(board[y + i][x] == 1 for i in range(5)):
                print(f"Player 1 wins vertically at ({x}, {y})")
                return 1
            if x + 4 < BOARD_SIZE and y + 4 < BOARD_SIZE and all(board[y + i][x + i] == 1 for i in range(5)):
                print(f"Player 1 wins diagonally (\\) at ({x}, {y})")
                return 1
            if x - 4 >= 0 and y + 4 < BOARD_SIZE and all(board[y + i][x - i] == 1 for i in range(5)):
                print(f"Player 1 wins diagonally (/) at ({x}, {y})")
                return 1
            if x + 4 < BOARD_SIZE and all(board[y][x + i] == 2 for i in range(5)):
                print(f"Player 2 wins horizontally at ({x}, {y})")
                return 2
            if y + 4 < BOARD_SIZE and all(board[y + i][x] == 2 for i in range(5)):
                print(f"Player 2 wins vertically at ({x}, {y})")
                return 2
            if x + 4 < BOARD_SIZE and y + 4 < BOARD_SIZE and all(board[y + i][x + i] == 2 for i in range(5)):
                print(f"Player 2 wins diagonally (\\) at ({x}, {y})")
                return 2
            if x - 4 >= 0 and y + 4 < BOARD_SIZE and all(board[y + i][x - i] == 2 for i in range(5)):
                print(f"Player 2 wins diagonally (/) at ({x}, {y})")
                return 2

    if all(board[y][x] != 0 for y in range(BOARD_SIZE) for x in range(BOARD_SIZE)):
        return 0

    return -1

def get_best_move_from_model(board):
    # print(board)  # 打印当前棋盘状态
    url = MODEL_URL
    messages = [
        {
            "role": "user",
            "content": f"现在正在进行一场五子棋游戏，棋盘为以索引0开始的二维数组，这是当前棋盘状态：{board}。数组值0表示空位，1表示玩家的棋子，2表示你的棋子。请给出接下来的最佳下棋位置，并确保该位置是空位。最后只给出棋子索引位置，不要任何其它文字内容。"
        }
    ]
    
    max_attempts = 10  # 最大循环次数
    attempts = 0

    while attempts < max_attempts:  # 限制循环次数
        attempts += 1
        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "stream": False,
            "max_tokens": 50,
            "temperature": 0.1,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "prompt": "你是一位五子棋的下棋高手，明白所有五子棋的规则，你知道如何封堵棋路来阻止玩家获胜，并且也知道如何在下一步中获胜。现在你需要判断当前棋盘状态，然后给出接下来的最佳下棋位置。",
            "messages": messages
        }
        headers = {
            "Authorization": AUTHORIZATION,
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        response_data = response.json()
        best_move = response_data["choices"][0]["message"]["content"]
        print(f"messages: {messages}")
        print(f"模型返回: {best_move}")
        
        try:
            # 提取文字中的坐标位置
            match = re.search(r'(\d+),\s*(\d+)', best_move)
            if match:
                x, y = map(int, match.groups())
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    if board[y][x] == 0:  # 检查模型返回的位置是否为空
                        return x, y
                    else:
                        print(f"模型返回的位置 [{x}, {y}] 已经有棋子，重新请求位置...")
                        messages.append({
                            "role": "user",
                            "content": f"你刚刚下棋的位置是[{x}, {y}]，该位置已经有棋子了，请重新判断最佳下棋位置来阻止玩家获胜，然后只给出棋子的索引位置。"
                        })
                else:
                    print(f"模型返回的位置 [{x}, {y}] 超出棋盘范围，重新请求位置...")
                    messages.append({
                        "role": "user",
                        "content": f"你刚刚下棋的位置是[{x}, {y}]，该位置超出了棋盘范围，请重新判断最佳下棋位置来阻止玩家获胜，然后只给出棋子的索引位置。"
                    })
            else:
                print("无法解析模型返回的坐标，重新请求位置...")
                messages.append({
                    "role": "user",
                    "content": "无法解析你刚刚返回的坐标，请重新判断最佳下棋位置，然后只给出棋子的索引位置。"
                })
        except (ValueError, IndexError) as e:
            print(f"解析模型返回时发生错误: {e}，重新请求位置...")
            messages.append({
                "role": "user",
                "content": "解析你刚刚返回的答案时发生错误，请重新判断最佳下棋位置，然后只给出棋子的索引位置。"
            })

    # 如果超过最大尝试次数，抛出异常
    raise ValueError("模型未能在最大尝试次数内返回有效的下棋位置")


def computer_move():
    try:
        x, y = get_best_move_from_model(board)
        if board[y][x] == 0:
            print(f"电脑下棋位置: [{x}, {y}]")  # 电脑下棋位置
            board[y][x] = 2  # 电脑下棋，设置为2
            draw_board()  # 添加绘制棋盘的调用
            pygame.display.flip()  # 刷新显示
            if check_win(board) == 2:
                show_message("电脑胜利!")
    except ValueError as e:
        print(f"模型返回错误: {e}")

# 游戏主循环
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and selected_x > 0:
                selected_x -= 1
            elif event.key == pygame.K_RIGHT and selected_x < BOARD_SIZE - 1:
                selected_x += 1
            elif event.key == pygame.K_UP and selected_y > 0:
                selected_y -= 1
            elif event.key == pygame.K_DOWN and selected_y < BOARD_SIZE - 1:
                selected_y += 1
            elif event.key == pygame.K_RETURN:
                if board[selected_y][selected_x] == 0 and player_turn:
                    print(f"玩家下棋位置: [{selected_x}, {selected_y}]")  # 打印玩家下棋位置
                    board[selected_y][selected_x] = 1  # 玩家下棋，设置为1
                    draw_board()
                    pygame.display.flip()
                    if check_win(board) == 1:
                        show_message("玩家胜利!")
                    player_turn = False  # 切换到电脑回合

    if not player_turn:
        computer_move()
        player_turn = True  # 切换到玩家回合

    draw_board()
    pygame.display.flip()
