# ============================================================
#  db.py — ชั้นติดต่อฐานข้อมูล
#  ใช้ %s เป็น placeholder เสมอ (กัน SQL injection)
# ============================================================
import mysql.connector
import config

# สถานะออเดอร์ที่ถือว่า "ยังใช้โต๊ะอยู่" (ตรงกับ ENUM ใน schema.sql)
ACTIVE_STATUSES = ("PENDING", "IN_PROGRESS")


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
    ใช้กับคอลัมน์ที่ว่างได้ เช่น order_time เพราะ MySQL ไม่รับ '' เป็น DATETIME"""
    return None if value in ("", None) else value


# ---------- ลูกค้า (customer) ----------
def search_customers(filters):
    """ค้นหาลูกค้าตามเงื่อนไข (name, phone, member_tier)"""
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
    """เพิ่มลูกค้าใหม่ — data มีคีย์: name, phone, member_tier"""
    sql = "INSERT INTO customer (name, phone, member_tier) VALUES (%s, %s, %s)"
    params = (data["name"], data["phone"], data["member_tier"])
    return run_command(sql, params)


def update_customer(cust_id, data):
    """แก้ไขลูกค้าตาม cust_id"""
    sql = "UPDATE customer SET name=%s, phone=%s, member_tier=%s WHERE cust_id=%s"
    params = (data["name"], data["phone"], data["member_tier"], cust_id)
    return run_command(sql, params)


def delete_customer(cust_id):
    """ลบลูกค้าตาม cust_id"""
    sql = "DELETE FROM customer WHERE cust_id=%s"
    return run_command(sql, (cust_id,))


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
    """ดึงเมนู 1 รายการตาม item_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    sql = "SELECT * FROM menu_item WHERE item_id = %s"
    rows = run_query(sql, (item_id,))
    return rows[0] if rows else None


def create_item(data):
    """เพิ่มเมนูใหม่ — data มีคีย์: name, category, price, is_available"""
    sql = ("INSERT INTO menu_item (name, category, price, is_available) "
           "VALUES (%s, %s, %s, %s)")
    params = (data["name"], data["category"], data["price"], data["is_available"])
    return run_command(sql, params)


def update_item(item_id, data):
    """แก้ไขเมนูตาม item_id"""
    sql = ("UPDATE menu_item SET name=%s, category=%s, price=%s, is_available=%s "
           "WHERE item_id=%s")
    params = (data["name"], data["category"], data["price"],
              data["is_available"], item_id)
    return run_command(sql, params)


def delete_item(item_id):
    """ลบเมนูตาม item_id"""
    sql = "DELETE FROM menu_item WHERE item_id=%s"
    return run_command(sql, (item_id,))


# ---------- ชุดคอมโบ (combo) ----------
def search_combos(filters):
    """ค้นหาส่วนประกอบของชุดคอมโบตามรหัสหรือชื่อเมนู"""
    sql = """SELECT c.item_id, combo_item.name AS combo_name,
                    c.sub_item_id, sub_item.name AS sub_item_name, c.amount
             FROM combo c
             INNER JOIN menu_item combo_item ON c.item_id = combo_item.item_id
             INNER JOIN menu_item sub_item ON c.sub_item_id = sub_item.item_id
             WHERE 1=1"""
    params = []

    if filters.get("item_id"):
        sql += " AND c.item_id = %s"
        params.append(filters["item_id"])

    if filters.get("sub_item_id"):
        sql += " AND c.sub_item_id = %s"
        params.append(filters["sub_item_id"])

    if filters.get("combo_name"):
        sql += " AND combo_item.name LIKE %s"
        params.append("%" + filters["combo_name"] + "%")

    if filters.get("sub_item_name"):
        sql += " AND sub_item.name LIKE %s"
        params.append("%" + filters["sub_item_name"] + "%")

    sql += " ORDER BY c.item_id, c.sub_item_id"
    return run_query(sql, params)


def get_combo(item_id, sub_item_id):
    """ดึงส่วนประกอบ 1 รายการจากชุดคอมโบ"""
    sql = ("SELECT item_id, sub_item_id, amount FROM combo "
           "WHERE item_id = %s AND sub_item_id = %s")
    rows = run_query(sql, (item_id, sub_item_id))
    return rows[0] if rows else None


def create_combo(data):
    """เพิ่มเมนูย่อยลงในชุดคอมโบ — data มีคีย์: item_id, sub_item_id, amount"""
    sql = ("INSERT INTO combo (item_id, sub_item_id, amount) "
           "VALUES (%s, %s, %s)")
    params = (data["item_id"], data["sub_item_id"], data["amount"])
    return run_command(sql, params)


def update_combo(item_id, sub_item_id, data):
    """แก้จำนวนเมนูย่อยในชุดคอมโบ"""
    sql = ("UPDATE combo SET amount = %s "
           "WHERE item_id = %s AND sub_item_id = %s")
    params = (data["amount"], item_id, sub_item_id)
    return run_command(sql, params)


def delete_combo(item_id, sub_item_id):
    """ลบเมนูย่อยออกจากชุดคอมโบ"""
    sql = "DELETE FROM combo WHERE item_id = %s AND sub_item_id = %s"
    return run_command(sql, (item_id, sub_item_id))


# ---------- ออเดอร์ (food_order) ----------
def search_orders(filters):
    # ยอดรวมคำนวณจาก unit_price (ราคาตอนสั่งจริง) ไม่ใช่ราคาเมนูปัจจุบัน
    sql = """SELECT o.order_id, o.cust_id, c.name AS customer_name,
                    o.table_id, o.order_time, o.status,
                    IFNULL(order_totals.total, 0) AS total
             FROM food_order o
             JOIN customer c ON o.cust_id = c.cust_id
             LEFT JOIN (SELECT oi.order_id, SUM(oi.qty * oi.unit_price) AS total
                        FROM order_item oi
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
    """ดึงออเดอร์ 1 รายการตาม order_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    sql = "SELECT * FROM food_order WHERE order_id = %s"
    rows = run_query(sql, (order_id,))
    return rows[0] if rows else None


def check_table_free(table_id, order_id=None):
    """เช็กว่าโต๊ะมีอยู่จริงและไม่มีออเดอร์ที่ยังไม่เสร็จ (PENDING / IN_PROGRESS)"""
    rows = run_query("SELECT 1 FROM dining_table WHERE table_id = %s", (table_id,))
    if not rows:
        raise ValueError(f"โต๊ะ {table_id} ไม่มีอยู่จริง")

    rows = run_query(
        "SELECT COUNT(*) AS n FROM food_order "
        "WHERE table_id = %s AND status IN ('PENDING', 'IN_PROGRESS') "
        "AND order_id <> %s",
        (table_id, order_id or 0))
    if rows[0]["n"] > 0:
        raise ValueError(f"โต๊ะ {table_id} ยังมีออเดอร์ที่ยังไม่เสร็จสิ้น")


def create_order(data):
    if data["status"] in ACTIVE_STATUSES:
        check_table_free(data["table_id"])

    sql = ("INSERT INTO food_order (cust_id, table_id, order_time, status) "
           "VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s)")
    params = (data["cust_id"], data["table_id"],
              blank_to_none(data.get("order_time")), data["status"])
    return run_command(sql, params)


def update_order(order_id, data):
    if data.get("status") in ACTIVE_STATUSES:
        check_table_free(data["table_id"], order_id)

    sql = ("UPDATE food_order SET cust_id=%s, table_id=%s, "
           "order_time=COALESCE(%s, order_time), status=%s WHERE order_id=%s")
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
    sql = """SELECT
                (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
                (SELECT COUNT(*) FROM menu_item) AS 'เมนู',
                (SELECT COUNT(*) FROM food_order) AS 'ออเดอร์',
                (SELECT IFNULL(SUM(qty * unit_price), 0)
                 FROM order_item) AS 'ยอดขายรวม',
                (SELECT COUNT(*) FROM dining_table) AS 'โต๊ะทั้งหมด',
                (SELECT COUNT(*) FROM menu_item WHERE is_available = 1) AS 'เมนูที่พร้อมขาย'
            """
    return run_query(sql)[0]


def report_popular_items():
    """📈 เมนูขายดี (Best Sellers)"""
    sql = """SELECT mi.name AS 'เมนู', SUM(oi.qty) AS 'จำนวนขาย'
             FROM order_item oi
             INNER JOIN menu_item mi ON oi.item_id = mi.item_id
             GROUP BY mi.item_id, mi.name
             ORDER BY SUM(oi.qty) DESC
             LIMIT 5"""
    return run_query(sql)


def report_daily_sales():
    """💰 ยอดขายรวมต่อวัน (Daily Sales)"""
    sql = """SELECT DATE(o.order_time) AS 'วันที่',
                    IFNULL(SUM(oi.qty * oi.unit_price), 0) AS 'ยอดขายรวม'
             FROM food_order o
             INNER JOIN order_item oi ON o.order_id = oi.order_id
             GROUP BY DATE(o.order_time)
             ORDER BY DATE(o.order_time)"""
    return run_query(sql)


def report_big_orders():
    """🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)"""
    # หมายเหตุ: ใน SQL ต้องเรียง GROUP BY -> HAVING -> ORDER BY
    sql = """SELECT o.order_id AS 'รหัสออเดอร์', c.name AS 'ชื่อลูกค้า',
                    SUM(oi.qty * oi.unit_price) AS 'ยอดขายรวม'
             FROM food_order o
             INNER JOIN customer c ON o.cust_id = c.cust_id
             INNER JOIN order_item oi ON o.order_id = oi.order_id
             GROUP BY o.order_id, c.name
             HAVING SUM(oi.qty * oi.unit_price) > 500
             ORDER BY SUM(oi.qty * oi.unit_price) DESC"""
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
]