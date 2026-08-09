def main():
    str_input = input("Nhap chuoi str_input: ")
 
    # Tap ky tu dac biet theo de bai: ! @ # $ % ^ & * ( ) - = + . /
    dac_biet_set = set("!@#$%^&*()-=+./")
 
    ky_tu_dac_biet = []
    ky_tu_chu_thuong = []
    ky_tu_chu_so = []
    ky_tu_chu_hoa = []
 
    for c in str_input:
        if c in dac_biet_set:
            ky_tu_dac_biet.append(c)
        elif 'a' <= c <= 'z':
            ky_tu_chu_thuong.append(c)
        elif '0' <= c <= '9':
            ky_tu_chu_so.append(c)
        elif 'A' <= c <= 'Z':
            ky_tu_chu_hoa.append(c)
 
    print("\n--- Ky tu dac biet:", " ".join(ky_tu_dac_biet))
    print("--- Ky tu chu thuong [a-z]:", " ".join(ky_tu_chu_thuong))
    print("--- Ky tu chu so [0-9]:", " ".join(ky_tu_chu_so))
    print("--- Ky tu chu hoa [A-Z]:", " ".join(ky_tu_chu_hoa))
    print("\n================ KET QUA ================")
    print(f"Do dai chuoi           : {len(str_input)}")
    print(f"So ky tu dac biet      : {len(ky_tu_dac_biet)}")
    print(f"So ky tu chu thuong    : {len(ky_tu_chu_thuong)}")
    print(f"So ky tu chu so        : {len(ky_tu_chu_so)}")
    print(f"So ky tu chu hoa       : {len(ky_tu_chu_hoa)}")
 
 
if __name__ == "__main__":
    main()
