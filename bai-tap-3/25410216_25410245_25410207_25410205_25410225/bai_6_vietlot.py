import random

def tao_day_so_random():
    dayso = ()
    while len(dayso) < 6:
        so = random.randint(1, 45)
        while so in dayso:
            so = random.randint(1, 45)
        dayso = dayso + (so, )
    return dayso

def chon_day_so():
    dayso = ()
    while len(dayso) < 6:
        so = int(input("Chon so tu 1 den 45: "))
        while so in dayso or not (1 <= so <= 45):
            so = int(input("So da ton tai hoac khong hop le, chon so tu 1 den 45: "))
        dayso = dayso + (so, )
        print(f"Day so cua ban la: {dayso}")
    return dayso

def do_so_trung(day_so_1, day_so_2):
    count = 0
    for so in day_so_1:
        if so in day_so_2:
            count += 1
    return count

def tinh_loi_lai(list_day_so_nguoi_mua, day_so_trung):
    tien_loi_lo = -len(list_day_so_nguoi_mua) * 10000

    for so_nguoi_mua in list_day_so_nguoi_mua:
        ket_qua = do_so_trung(so_nguoi_mua, day_so_trung)

        if ket_qua == 3:
            tien_loi_lo += 30000
        elif ket_qua == 4:
            tien_loi_lo += 300000
        elif ket_qua == 5:
            tien_loi_lo += 10000000
        elif ket_qua == 6:
            tien_loi_lo += 10000000000

    return tien_loi_lo

def main():
    n = 1

    list_day_so_nguoi_mua = [chon_day_so() for _ in range(n)]
    day_so_trung_thuong = tao_day_so_random()

    print(f"Day so trung thuong: {day_so_trung_thuong}")

    loi_lai = tinh_loi_lai(list_day_so_nguoi_mua, day_so_trung_thuong)

    print(f"So tien ban nhan duoc la: {loi_lai}")


if __name__ == '__main__':
    main()