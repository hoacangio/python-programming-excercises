import random

moves = ['keo', 'bao', 'bua']

def get_random_move():
    return random.choice(moves)

def play():

    input1 = input("Chon keo, bua hoac bao: ")

    while not (input1 in moves):
        input1 = input("Ban da nhap sai, chon keo, bua hoac bao: ")

    input2 = get_random_move()

    print(f"Ban chon [{input1}], may chon [{input2}]")

    while input1 == input2:
        print("Hoa")

    if (input1 == 'keo' and input2 == 'bao') or (input1 == 'bua' and input2 == 'keo') or (input1 == 'bao' and input2 == 'bua'):
        print("Ban da thang")
    else:
        print("Ban da thua")

def main():
    play()


if __name__ == '__main__':
    main()