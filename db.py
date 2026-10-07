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

  #ทำถึงตรงนี้

def create_customer(data):
    """เพิ่ม ลูกค้า ใหม่ — data มีคีย์: name, phone, member_tier"""
    # TODO: INSERT INTO customer (...) VALUES (%s, ...)
    _todo("create_customer")


def update_customer(cust_id, data):
    """แก้ไข ลูกค้า ตาม cust_id"""
    # TODO: UPDATE customer SET ... WHERE cust_id=%s
    _todo("update_customer")


def delete_customer(cust_id):
    """ลบ ลูกค้า ตาม cust_id"""
    # TODO: DELETE FROM customer WHERE cust_id=%s
    _todo("delete_customer")

# ---------- เมนูอาหาร (menu_item) ----------
def search_items(filters):
    """ค้นหา เมนูอาหาร ตามเงื่อนไข (name, category)
    คำใบ้: เริ่มจาก sql = "SELECT * FROM menu_item WHERE 1=1"
    แล้วต่อเงื่อนไขเฉพาะ filter ที่มีค่า (ข้อความใช้ LIKE %s, อื่น ๆ ใช้ = %s)"""
    # TODO: เขียน SQL ค้นหาแบบยืดหยุ่นตาม filters (ใช้ %s เสมอ)
    _todo("search_items")


def get_item(item_id):
    """ดึง เมนูอาหาร 1 รายการตาม item_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    # TODO: SELECT * FROM menu_item WHERE item_id = %s แล้วคืนแถวเดียว
    _todo("get_item")


def create_item(data):
    """เพิ่ม เมนูอาหาร ใหม่ — data มีคีย์: name, category, price, is_available"""
    # TODO: INSERT INTO menu_item (...) VALUES (%s, ...)
    _todo("create_item")


def update_item(item_id, data):
    """แก้ไข เมนูอาหาร ตาม item_id"""
    # TODO: UPDATE menu_item SET ... WHERE item_id=%s
    _todo("update_item")


def delete_item(item_id):
    """ลบ เมนูอาหาร ตาม item_id"""
    # TODO: DELETE FROM menu_item WHERE item_id=%s
    _todo("delete_item")

# ---------- ออเดอร์ (food_order) ----------
def search_orders(filters):
    """ค้นหา ออเดอร์ ตามเงื่อนไข (cust_id, table_id, status)
    ต้องแสดงคอลัมน์: order_id, cust_id, ชื่อลูกค้า, table_id, order_time, status, total (ยอดรวม)
    คำใบ้:
      - JOIN customer เพื่อแสดงชื่อลูกค้า
      - total (ยอดรวมของออเดอร์) ไม่ได้เก็บเป็นคอลัมน์ → ต้องคำนวณ = SUM(qty × price)
        LEFT JOIN กับ subquery ที่รวมยอดของแต่ละ order_id (order_item JOIN menu_item ... GROUP BY order_id)
        แล้วใช้ IFNULL(..., 0) เพราะออเดอร์ที่ยังไม่มีรายการอาหารจะได้ NULL
      - เงื่อนไขทุกตัวใช้ = %s"""
    # TODO: เขียน SQL ค้นหาแบบยืดหยุ่นตาม filters (ใช้ %s เสมอ)
    _todo("search_orders")


def get_order(order_id):
    """ดึง ออเดอร์ 1 รายการตาม order_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    # TODO: SELECT * FROM food_order WHERE order_id = %s แล้วคืนแถวเดียว
    _todo("get_order")


def check_table_free(table_id, order_id=None):
    """ตรวจก่อนเปิดออเดอร์ (status = 'open') — ถ้าไม่ผ่านให้ raise ValueError("ข้อความ")
    (หน้าเว็บจะแสดงข้อความนั้นเป็น alert ให้ผู้ใช้เห็น และไม่บันทึกข้อมูล)
    1) โต๊ะต้องมีอยู่จริง → SELECT ... FROM dining_table WHERE table_id = %s
    2) โต๊ะต้องว่าง = ไม่มีออเดอร์อื่นที่ยัง 'open' อยู่ที่โต๊ะนี้
       → SELECT COUNT(*) AS n FROM food_order WHERE table_id = %s AND status = 'open' AND order_id <> %s
       ★ ตอนเพิ่มใหม่ order_id เป็น None → ส่ง 0 แทน (order_id or 0) จะได้ไม่ตรงกับออเดอร์ไหนเลย
    ตัวอย่าง: raise ValueError(f"โต๊ะ {table_id} ยังมีออเดอร์ที่ยังไม่ชำระเงิน")"""
    # TODO: เขียนการตรวจ 2 ข้อตามคำใบ้
    _todo("check_table_free")


def create_order(data):
    """เพิ่ม ออเดอร์ ใหม่ — data มีคีย์: cust_id, table_id, order_time, status
    คำใบ้:
      1) ถ้า status = 'open' → เรียก check_table_free(data["table_id"]) ก่อน (โต๊ะต้องว่าง)
      2) INSERT INTO food_order (...) VALUES (%s, ...)
         (order_time ว่างได้ → blank_to_none(data["order_time"]))"""
    # TODO: เขียนตามคำใบ้
    _todo("create_order")


def update_order(order_id, data):
    """แก้ไข ออเดอร์ ตาม order_id
    คำใบ้:
      1) ถ้า status ใหม่ = 'open' → check_table_free(data["table_id"], order_id)
         (ส่ง order_id ไปด้วย เพื่อไม่นับออเดอร์ตัวเอง)
      2) UPDATE food_order SET ... WHERE order_id=%s"""
    # TODO: เขียนตามคำใบ้
    _todo("update_order")


def delete_order(order_id):
    """ลบ ออเดอร์ ตาม order_id"""
    # TODO: DELETE FROM food_order WHERE order_id=%s
    _todo("delete_order")


# ============================================================
#  REPORT (รายงาน — ใช้ JOIN + GROUP BY + subquery)
#  ★ ชื่อคอลัมน์ใน SELECT จะกลายเป็นหัวตารางบนเว็บ — ใช้ AS 'ชื่อภาษาไทย' ได้
# ============================================================
def report_summary():
    """ตัวเลขสรุปบนการ์ด dashboard — คืน dict {ชื่อการ์ด: ตัวเลข}  (1 คีย์ = 1 การ์ด)
    ตอนนี้ยังไม่ได้เขียน SQL → คืนค่า None ทุกการ์ด หน้าเว็บจึงแสดง "—" รอไว้
    ★ งานของนิสิต: เขียน SQL ตามตัวอย่างด้านล่าง (1 คอลัมน์ใน SELECT = 1 การ์ด
      ชื่อหลัง AS = ข้อความใต้ตัวเลข) แล้วลบ return {...} ชุดล่างสุดทิ้ง
    ★ การ์ด "คิดเพิ่มเอง" 2 ใบ: ตั้งชื่อการ์ดใหม่ แล้วเขียน SQL เอง
    ★ ผลรวมเงินใช้ IFNULL(SUM(...), 0) — ถ้ายังไม่มีข้อมูล SUM จะได้ NULL"""
    # ---- ตัวอย่างเมื่อเขียน SQL แล้ว (เอา # ข้างหน้าออก แล้วเติมให้ครบทุกการ์ด) ----
    # sql = """SELECT
    #            (SELECT COUNT(*) FROM ...) AS 'ลูกค้า',
    #            (SELECT ...)               AS 'เมนู',
    #            ...
    #          """
    # return run_query(sql)[0]      ← [0] = เอาแถวแรก (ผลมีแถวเดียว) ได้เป็น dict

    # TODO: ระหว่างที่ยังไม่ได้เขียน SQL คืนค่า None ให้การ์ดแสดง "—" รอไว้
    return {
        "ลูกค้า":         None,   # (SELECT COUNT(*) FROM customer)
        "เมนู":           None,   # นับเมนูทั้งหมด
        "ออเดอร์":        None,   # นับออเดอร์ทั้งหมด
        "ยอดขายรวม":      None,   # IFNULL(SUM(qty × price), 0) จาก order_item JOIN menu_item
        "คิดเพิ่มเอง 1":  None,   # ตั้งชื่อการ์ดใหม่ + เขียน SQL เอง
        "คิดเพิ่มเอง 2":  None,   # ตั้งชื่อการ์ดใหม่ + เขียน SQL เอง
    }

def report_popular_items():
    """📈 เมนูขายดี (Best Sellers)
    คำใบ้: JOIN order_item→menu_item, GROUP BY item, SUM(qty), ORDER BY DESC, LIMIT 5"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    _todo("report_popular_items")

def report_daily_sales():
    """💰 ยอดขายรวมต่อวัน (Daily Sales)
    คำใบ้: JOIN food_order→order_item→menu_item, GROUP BY วันที่, SUM(qty*price)"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    _todo("report_daily_sales")

def report_big_orders():
    """🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)
    คำใบ้: GROUP BY order, HAVING SUM(qty*price) > 500"""
    # TODO: เขียน SQL รายงานนี้ (เขียน JOIN แบบ explicit INNER JOIN ... ON ...)
    _todo("report_big_orders")

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
