# ============================================================
#  db.py — ชั้นติดต่อฐานข้อมูล  ★★★ นิสิตเขียน SQL ในไฟล์นี้ ★★★
#  มองหาคำว่า  # TODO  ทุกฟังก์ชัน — ใช้ %s เป็น placeholder เสมอ (กัน SQL injection)
# ============================================================
import mysql.connector
import config


def get_connection():
    return mysql.connector.connect(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, port=config.DB_PORT)


def run_query(sql, params=None):
    """รัน SELECT คืนผลเป็น list ของ dict"""
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ()); rows = cur.fetchall()
    cur.close(); conn.close(); return rows


def run_command(sql, params=None):
    """รัน INSERT / UPDATE / DELETE แล้ว commit"""
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params or ()); conn.commit()
    out = {"new_id": cur.lastrowid, "affected": cur.rowcount}
    cur.close(); conn.close(); return out


def blank_to_none(value):
    """ช่องที่ไม่ได้กรอกในฟอร์มจะส่งมาเป็น "" — แปลงเป็น None (= NULL ใน SQL)
    ใช้กับคอลัมน์ที่ว่างได้ เช่น return_date, paid_date  เพราะ MySQL ไม่รับ '' เป็น DATE"""
    return None if value in ("", None) else value


def _todo(name):
    raise NotImplementedError(f"TODO: ยังไม่ได้เขียนฟังก์ชัน {name} ใน db.py")


# ---------- ลูกค้า (customer) ----------
def search_customers(filters):
    """ค้นหา ลูกค้า ตามเงื่อนไข (name, phone, member_tier)
    คำใบ้: เริ่มจาก sql = "SELECT * FROM customer WHERE 1=1"
    แล้วต่อเงื่อนไขเฉพาะ filter ที่มีค่า (ข้อความใช้ LIKE %s, อื่น ๆ ใช้ = %s)"""

    sql = "SELECT * FROM customer WHERE 1=1"
    params = []

    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append("%" + filters["name"] + "%")

    if filters.get("phone"):
        sql += " AND phone LIKE %s"
        params.append("%" + filters["phone"] + "%")

    if filters.get("member_tier"):
        sql += " AND member_tier = %s"
        params.append(filters["member_tier"])

    return run_query(sql, params)


def get_customer(cust_id):
    sql = "SELECT * FROM customer WHERE cust_id = %s"
    rows = run_query(sql, (cust_id,))
    return rows[0] if rows else None

 

def create_customer(data):
    """เพิ่ม ลูกค้า ใหม่ — data มีคีย์: name, phone, member_tier"""
    # TODO: INSERT INTO customer (...) VALUES (%s, ...)
    sql =" INSERT INTO customer (name, phone, member_tier) VALUES (%s,%s,%s)"
    params = (data["name"], data["phone"], data["member_tier"])
    return run_command(sql, params)
   


def update_customer(cust_id, data):
    """แก้ไข ลูกค้า ตาม cust_id"""
    # TODO: UPDATE customer SET ... WHERE cust_id=%s
    sql = "UPDATE customer SET name=%s, phone=%s, member_tier=%s WHERE cust_id=%s"
    params =(data["name"], data["phone"], data["member_tier"], cust_id)
    return run_command(sql, params)
   


def delete_customer(cust_id):
    """ลบ ลูกค้า ตาม cust_id"""
    # TODO: DELETE FROM customer WHERE cust_id=%s
    sql = "DELETE FROM customer WHERE cust_id=%s"
    return run_command(sql,(cust_id,))

   

# ---------- เมนูอาหาร (menu_item) ----------
def search_items(filters):

    sql = "SELECT * FROM menu_item WHERE 1=1"
    params = []

    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append("%" + filters["name"] + "%")

    if filters.get("category"):
        sql += " AND category = %s"
        params.append(filters["category"])

    return run_query(sql, params)

def get_item(item_id):
    """ดึง เมนูอาหาร 1 รายการตาม item_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    # TODO: SELECT * FROM menu_item WHERE item_id = %s แล้วคืนแถวเดียว
    sql = "SELECT * FROM menu_item WHERE item_id = %s"
    rows = run_query(sql, (item_id,))
    return rows[0] if rows else None
   


def create_item(data):
    """เพิ่ม เมนูอาหาร ใหม่ — data มีคีย์: name, category, price, is_available"""
    # TODO: INSERT INTO menu_item (...) VALUES (%s, ...)
    sql = "INSERT INTO menu_item (name, category, price, is_available) VALUES (%s,%s,%s,%s)"
    params =(data["name"], data["category"], data["price"],data["is_available"])
    return run_command(sql, params)

   


def update_item(item_id, data):
    """แก้ไข เมนูอาหาร ตาม item_id"""
    # TODO: UPDATE menu_item SET ... WHERE item_id=%s
    sql = "UPDATE menu_item SET name=%s, category=%s, price=%s, is_available=%s WHERE item_id=%s"
    params =(data["name"], data["category"], data["price"],data["is_available"], item_id)
    return run_command(sql, params)
    
  


def delete_item(item_id):
    """ลบ เมนูอาหาร ตาม item_id"""
    # TODO: DELETE FROM menu_item WHERE item_id=%s
    sql = "DELETE FROM menu_item WHERE item_id=%s"
    return run_command(sql, (item_id,))
   

# ---------- ออเดอร์ (food_order) ----------
def search_orders(filters):
    sql = """SELECT o.order_id, o.cust_id, c.name AS customer_name,
                    o.table_id, o.order_time, o.status,
                    IFNULL(order_totals.total, 0) AS total
             FROM food_order o
             JOIN customer c ON o.cust_id = c.cust_id
             LEFT JOIN (SELECT oi.order_id, SUM(oi.qty * mi.price) AS total
                        FROM order_item oi
                        JOIN menu_item mi ON oi.item_id = mi.item_id
                        GROUP BY oi.order_id) AS order_totals
                    ON o.order_id = order_totals.order_id
             WHERE 1=1"""
    params = []

    if filters.get("cust_id"):
        sql += " AND o.cust_id = %s"
        params.append(filters["cust_id"])

    if filters.get("table_id"):
        sql += " AND o.table_id = %s"
        params.append(filters["table_id"])

    if filters.get("status"):
        sql += " AND o.status = %s"
        params.append(filters["status"])

    return run_query(sql, params)


def get_order(order_id):
    """ดึง ออเดอร์ 1 รายการตาม order_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    # TODO: SELECT * FROM food_order WHERE order_id = %s แล้วคืนแถวเดียว
    sql = "SELECT * FROM food_order WHERE order_id = %s"
    rows =run_query(sql, (order_id,))
    return rows[0] if rows else None
  


def check_table_free(table_id, order_id=None):
    rows = run_query("SELECT * FROM dining_table WHERE table_id = %s", (table_id,))
    if not rows:
        raise ValueError(f"โต๊ะ {table_id} ไม่มีอยู่จริง")

    rows = run_query(
        "SELECT COUNT(*) AS n FROM food_order "
        "WHERE table_id = %s AND status = 'open' AND order_id <> %s",
        (table_id, order_id or 0))
    if rows[0]["n"] > 0:
        raise ValueError(f"โต๊ะ {table_id} ยังมีออเดอร์ที่ยังไม่ชำระเงิน")


def create_order(data):
    if data["status"] == "open":
        check_table_free(data["table_id"])

    sql = "INSERT INTO food_order (cust_id, table_id, order_time, status) VALUES (%s, %s, %s, %s)"
    params = (data["cust_id"], data["table_id"],
              blank_to_none(data.get("order_time")), data["status"])
    return run_command(sql, params)


  


def update_order(order_id, data):
    if data.get("status") == "open":
        check_table_free(data["table_id"], order_id)

    sql = "UPDATE food_order SET cust_id=%s, table_id=%s, order_time=%s, status=%s WHERE order_id=%s"
    params = (data["cust_id"], data["table_id"],
              blank_to_none(data.get("order_time")), data["status"], order_id)
    return run_command(sql, params)

def delete_order(order_id):

    sql = "DELETE FROM food_order WHERE order_id=%s"
    return run_command(sql, (order_id,))

  


# ============================================================
#  REPORT (รายงาน — ใช้ JOIN + GROUP BY + subquery)
#  ★ ชื่อคอลัมน์ใน SELECT จะกลายเป็นหัวตารางบนเว็บ — ใช้ AS 'ชื่อภาษาไทย' ได้
# ============================================================
def report_summary():
#     """ตัวเลขสรุปบนการ์ด dashboard — คืน dict {ชื่อการ์ด: ตัวเลข}  (1 คีย์ = 1 การ์ด)
#     ตอนนี้ยังไม่ได้เขียน SQL → คืนค่า None ทุกการ์ด หน้าเว็บจึงแสดง "—" รอไว้
#     ★ งานของนิสิต: เขียน SQL ตามตัวอย่างด้านล่าง (1 คอลัมน์ใน SELECT = 1 การ์ด
#       ชื่อหลัง AS = ข้อความใต้ตัวเลข) แล้วลบ return {...} ชุดล่างสุดทิ้ง
#     ★ การ์ด "คิดเพิ่มเอง" 2 ใบ: ตั้งชื่อการ์ดใหม่ แล้วเขียน SQL เอง
#     ★ ผลรวมเงินใช้ IFNULL(SUM(...), 0) — ถ้ายังไม่มีข้อมูล SUM จะได้ NULL"""

    # ---- ตัวอย่างเมื่อเขียน SQL แล้ว (เอา # ข้างหน้าออก แล้วเติมให้ครบทุกการ์ด) ----
    # sql = """SELECT
    #            (SELECT COUNT(*) FROM ...) AS 'ลูกค้า',
    #            (SELECT ...)               AS 'เมนู',
    #            ...
    #          """
    # return run_query(sql)[0]      ← [0] = เอาแถวแรก (ผลมีแถวเดียว) ได้เป็น dict

    # TODO: ระหว่างที่ยังไม่ได้เขียน SQL คืนค่า None ให้การ์ดแสดง "—" รอไว้
  

    sql = """SELECT
                (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
                (SELECT COUNT(*) FROM menu_item) AS 'เมนู',
                (SELECT COUNT(*) FROM food_order) AS 'ออเดอร์',
                (SELECT IFNULL(SUM(oi.qty * mi.price), 0)
                 FROM order_item oi
                 JOIN menu_item mi ON oi.item_id = mi.item_id) AS 'ยอดขายรวม',
                (SELECT COUNT(*) FROM dining_table) AS 'โต๊ะทั้งหมด',
                (SELECT COUNT(*) FROM menu_item WHERE is_available = 1) AS 'เมนูที่พร้อมขาย'
            """
    return run_query(sql)[0]

def report_popular_items():
    """📈 เมนูขายดี (Best Sellers)
    คำใบ้: JOIN order_item→menu_item, GROUP BY item, SUM(qty), ORDER BY DESC, LIMIT 5"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    sql = """SELECT mi.name AS 'เมนู', sum(oi.qty) AS 'จำนวนขาย'
    FROM order_item oi
    INNER JOIN menu_item mi ON oi.item_id = mi.item_id
    GROUP BY mi.name
    ORDER BY sum(oi.qty) DESC
    LIMIT 5"""
    return run_query(sql)
  

def report_daily_sales():
    """💰 ยอดขายรวมต่อวัน (Daily Sales)
    คำใบ้: JOIN food_order→order_item→menu_item, GROUP BY วันที่, SUM(qty*price)"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    sql = """SELECT DATE(o.order_time) AS 'วันที่', IFNULL(SUM(oi.qty * mi.price), 0) AS 'ยอดขายรวม'
    FROM food_order o
    INNER JOIN order_item oi ON o.order_id = oi.order_id
    INNER JOIN menu_item mi ON oi.item_id = mi.item_id
    GROUP BY DATE(o.order_time)"""
    return run_query(sql)
  

def report_big_orders():
    """🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)
    คำใบ้: GROUP BY order, HAVING SUM(qty*price) > 500"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    sql = """SELECT o.order_id AS 'รหัสออเดอร์', c.name AS 'ชื่อลูกค้า', IFNULL(SUM(oi.qty * mi.price), 0) AS 'ยอดขายรวม'
    FROM food_order o
    INNER JOIN customer c ON o.cust_id = c.cust_id
    INNER JOIN order_item oi ON o.order_id = oi.order_id
    INNER JOIN menu_item mi ON oi.item_id = mi.item_id
    GROUP BY o.order_id,  c.name
    HAVING IFNULL(SUM(oi.qty * mi.price), 0)> 500"""
    return run_query(sql)

# ============================================================
#  รายการรายงานที่แสดงบนหน้า /report  (เรียงตามลำดับที่แสดง)
#  ★ วิธีเพิ่มรายงานใหม่ (ไม่ต้องแก้ไฟล์อื่น):
#    1) เขียนฟังก์ชัน report_xxx() ด้านบน ให้ return run_query(sql)
#    2) เพิ่ม 1 บรรทัดในรายการนี้:  ("ชื่อใน-url", "หัวข้อที่แสดง", ชื่อฟังก์ชัน)
#  ★ รายการนี้ต้องอยู่ท้ายไฟล์ (หลังฟังก์ชันทั้งหมด) ไม่งั้น Python หาชื่อฟังก์ชันไม่เจอ
#  ★ ห้ามตั้งชื่อ url ว่า "summary" (ใช้แล้วสำหรับการ์ดสรุป)
# ============================================================
REPORTS = [
    ("popular-items", "📈 เมนูขายดี (Best Sellers)",        report_popular_items),
    ("daily-sales",   "💰 ยอดขายรวมต่อวัน (Daily Sales)",   report_daily_sales),
    ("big-orders",    "🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)", report_big_orders),
    # ("my-report", "📋 รายงานของฉัน", report_my_report),   ← ตัวอย่างการเพิ่มรายงานที่ 4
]
