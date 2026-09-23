from mysql.connector import Error

from db_connection import get_connection
from mysql.connector.connection import MySQLConnection

def insert_nhan_vien(conn: MySQLConnection, ho_ten, phone, email, chuc_vu):
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO nhan_vien (ho_ten, phone, email, chuc_vu) VALUES (%s, %s, %s, %s)"
        values = (ho_ten, phone, email, chuc_vu)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
    except Error as e:
        print(f"Loi truy van SQL: {e}")
        return


def select_all_nhan_vien(conn: MySQLConnection):
    try:
        cursor = conn.cursor()
        sql = "SELECT ho_ten, phone, email, chuc_vu FROM nhan_vien" 
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
    except Error as e:
        print(f"Loi truy van SQL: {e}")
        return

def update_phone(conn: MySQLConnection, id_nv, phone_moi):
    try:
        cursor = conn.cursor()
        sql = "UPDATE nhan_vien SET phone = %s WHERE id_nv = %s"
        values = (phone_moi, id_nv)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
    except Error as e:
            print(f"Loi truy van SQL: {e}")
            return
    


def delete_nhan_vien(conn: MySQLConnection, id_nv):
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM nhan_vien WHERE id_nv = %s"
        values = (id_nv,)   
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
    except Error as e:
            print(f"Loi truy van SQL: {e}")
            return


def main():
    conn = get_connection()
    if conn is None:
        return

    try:
        print("Danh sach nhan vien truoc khi them moi:")
        select_all_nhan_vien(conn)
        insert_nhan_vien(conn, "Nguyen Van A", "0123456789", "a@gmail.com", "Nhan vien")
        insert_nhan_vien(conn, "Nguyen Van B", "0987654321", "b@gmail.com", "Quan ly")
        insert_nhan_vien(conn, "Nguyen Van C", "0111222333", "c@gmail.com", "Nhan vien")
        insert_nhan_vien(conn, "Nguyen Van D", "0222333444", "d@gmail.com", "Nhan vien")
        insert_nhan_vien(conn, "Nguyen Van E", "0333444555", "e@gmail.com", "Nhan vien")
        update_phone(conn, 1, "0999999999")
        delete_nhan_vien(conn, 2)
        print("Danh sach nhan vien sau khi them moi, cap nhat va xoa:")
        select_all_nhan_vien(conn)

    except Error as e:
        print(f"Loi truy van SQL: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
