
tenMHL = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com"
]

email = input("Nhập địa chỉ e-mail: ")

# Kiểm tra khoảng trắng
if " " in email:
    print("E-mail không hợp lệ vì có khoảng trắng!")

# Kiểm tra có ký tự @ hay không
elif "@" not in email:
    print("E-mail không hợp lệ vì không có ký tự @!")

# Kiểm tra có nhiều hơn 1 ký tự @
elif email.count("@") > 1:
    print("E-mail không hợp lệ vì có nhiều hơn một ký tự @!")

else:
    # Tách e-mail thành 2 phần tại ký tự @
    ten, mien_email = email.split("@")

    # Kiểm tra độ dài phần tên
    if len(ten) < 6:
        print("E-mail không hợp lệ vì phần tên phải có ít nhất 6 ký tự!")

    # Kiểm tra tên miền
    elif mien_email not in tenMHL:
        print("E-mail không hợp lệ vì tên miền không được hỗ trợ!")

    # Nếu thỏa mãn tất cả điều kiện
    else:
        print("E-mail hợp lệ!")