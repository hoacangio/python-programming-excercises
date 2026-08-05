import random

"""
CÁC ĐOẠN CODE SAU ĐỀU DO NGƯỜI VIẾT, KHÔNG SỬ DỤNG AI
"""

moves = ['keo', 'bao', 'bua']

def get_random_move():
    return random.choice(moves)

"""
Hàm nhận vào 1 cặp đấu và tìm ra người thắng cuộc
Nếu hòa thì sẽ chơi lại
"""
def play(pair):
    player1, player2 = pair
    ## Nếu player2 là -1 thì player1 là người thắng cuộc
    if player2 == -1:
        return player1

    input1 = get_random_move()
    input2 = get_random_move()

    print(f'===Match: Player {player1} vs Player {player2}')

    while input1 == input2:
        input1 = get_random_move()
        input2 = get_random_move()

    if (input1 == 'keo' and input2 == 'bao') or (input1 == 'bua' and input2 == 'keo') or (input1 == 'bao' and input2 == 'bua'):
        print(f'{input1} vs {input2} => Player {player1} wins!')
        print("===End Match\n", flush=True)
        return player1
    else:
        print(f'{input1} vs {input2} => Player {player2} wins!')
        print("===End Match\n", flush=True)
        return player2

"""
Hàm chia cặp đấu, mảng các người chơi và tự chia cặp, nếu là số lẻ thì người chơi cuối sẽ cặp với -1

get_pairs([1, 2, 3]) -> [(1, 2), (3, -1)]
get_pairs([1, 2, 3, 4]) -> [(1, 2), (3, 4)]

"""

def get_pairs(players):
    pairs = [(players[i], players[i + 1]) for i in range(0, len(players) - 1, 2)]

    if len(pairs) * 2 < len(players):
        pairs.append((players[-1], -1))

    return pairs

def print_pairs(pairs):
    print("===Matches:")
    for (player1, player2) in pairs:
        if player2 != -1:
            print(f'Player {player1} vs Player {player2}')

    print("===")

"""
Hàm chạy giải đấu, nhận vào số lượng người chơi, tạo ra danh sach người chơi (danh sách sô nguyên)
Sau đó danh sách được trộn lẫn
Tiếp theo được chia cặp, dùng hàm get_pair
Người thắng của mỗi cặp sẽ được vào vòng tiếp theo
Cho tới khi chỉ còn 1 căp với "người chơi" thứ 2 là -1 -> Nghĩa là người còn lại trong cặp đó là champion
"""
def league(number_of_players):
    players = list(range(number_of_players))
    random.shuffle(players)
    pairs = get_pairs(players)

    while not (len(pairs) == 1 and pairs[-1][1] == -1):
        print("===================START ROUND=======================")
        print_pairs(pairs)
        winners = [ play(pair) for pair in pairs ]
        pairs = get_pairs(winners)
        print("===================END ROUND=======================")

    print(f"Player {pairs[-1][0]} is the champion!!")


def main():
    league(number_of_players=random.randint(8, 20))


if __name__ == '__main__':
    main()