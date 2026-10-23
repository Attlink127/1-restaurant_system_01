# ============================================================
#  db.py — ชั้นติดต่อฐานข้อมูล
#  ใช้ %s เป็น placeholder เสมอ (กัน SQL injection)
# ============================================================
import mysql.connector
import config
from datetime import datetime
from decimal import Decimal

# สถานะออเดอร์ที่ถือว่า "ยังใช้โต๊ะอยู่" (ตรงกับ ENUM ใน schema.sql)
ACTIVE_STATUSES = ("PENDING", "IN_PROGRESS", "READY")


# ---------- ฟังก์ชันพื้นฐานสำหรับติดต่อฐานข้อมูล ----------
def get_connection():
    """เปิดการเชื่อมต่อ (Connection) ไปยังฐานข้อมูล MySQL
    โดยดึงค่าตั้งต้น (host/user/password/database/port) จากไฟล์ config.py"""
    return mysql.connector.connect(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, port=config.DB_PORT)


def run_query(sql, params=None):
    """รันคำสั่ง SELECT แล้วคืนผลลัพธ์เป็น list ของ dict
    - dictionary=True ทำให้แต่ละแถวออกมาเป็น dict เช่น {"name": "ข้าวผัด", "price": 50}
      จึงโยงกับชื่อคอลัมน์ที่ SELECT มาได้ตรง ๆ และกลายเป็นหัวตารางบนหน้าเว็บ
    - params ถูกส่งแยกจาก sql เพื่อกัน SQL Injection (ไม่เอาไปต่อสตริงเอง)
    - ปิด cursor และ connection ทุกครั้งเพื่อคืน resource ให้ฐานข้อมูล"""
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        if cur is not None:
            cur.close()
        conn.close()


def run_command(sql, params=None):
    """รันคำสั่งที่เปลี่ยนแปลงข้อมูล (INSERT / UPDATE / DELETE) แล้ว commit
    - ต้อง commit() ไม่งั้นข้อมูลจะไม่ถูกบันทึกจริงลงฐานข้อมูล
    - คืนค่า new_id (id ที่เพิ่ง insert ล่าสุด) และ affected (จำนวนแถวที่ถูกแก้/ลบ)
      เพื่อให้ฝั่งเว็บรู้ว่าทำงานสำเร็จ"""
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return {"new_id": cur.lastrowid, "affected": cur.rowcount}
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close()
        conn.close()


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
    """ดึงลูกค้า 1 รายตาม cust_id (คืน dict แถวเดียว หรือ None ถ้าไม่พบ)"""
    sql = "SELECT * FROM customer WHERE cust_id = %s"
    rows = run_query(sql, (cust_id,))
    return rows[0] if rows else None


def validate_phone(value):
    # เก็บเป็นข้อความเพื่อรักษาเลข 0 นำหน้า ตรวจที่ API ด้วยเพื่อกันส่งข้อมูลข้ามหน้าเว็บ
    if not isinstance(value, str) or len(value) != 10 or not value.isascii() or not value.isdigit():
        raise ValueError("กรุณากรอกเบอร์โทรเป็นตัวเลข 10 หลัก")
    return value


def validate_member_tier(value):
    """รับเฉพาะค่าที่ตรงกับ ENUM ของ customer ไม่ปล่อยให้ MySQL ตัดค่าผิด"""
    if not isinstance(value, str) or value not in ("Regular", "Gold", "VIP"):
        raise ValueError("กรุณาเลือกระดับสมาชิก Regular, Gold หรือ VIP")
    return value


def create_customer(data):
    """เลือกระดับเริ่มต้นได้จากฟอร์ม ถ้าไม่ส่งค่าให้ใช้ Regular"""
    tier = validate_member_tier(data.get("member_tier", "Regular"))
    return run_command(
        "INSERT INTO customer (name, phone, member_tier) VALUES (%s, %s, %s)",
        (data["name"], validate_phone(data.get("phone")), tier))


def update_customer(cust_id, data):
    """แก้ระดับเองได้; ถ้า API ไม่ส่งระดับ ให้คงค่าปัจจุบันไว้"""
    phone = validate_phone(data.get("phone"))
    if "member_tier" in data:
        tier = validate_member_tier(data["member_tier"])
        return run_command("UPDATE customer SET name=%s, phone=%s, member_tier=%s WHERE cust_id=%s",
                           (data["name"], phone, tier, cust_id))
    return run_command("UPDATE customer SET name=%s, phone=%s WHERE cust_id=%s",
                       (data["name"], phone, cust_id))


def delete_customer(cust_id):
    """ลบลูกค้าตาม cust_id"""
    try:
        sql = "DELETE FROM customer WHERE cust_id=%s"
        return run_command(sql, (cust_id,))
    except mysql.connector.Error as err:
        if err.errno == 1451:
            raise ValueError("ไม่สามารถลบลูกค้ารายนี้ได้ เนื่องจากมีประวัติออเดอร์ในระบบ")
        raise


# ---------- เมนูอาหาร (menu_item) ----------
def search_items(filters):
    """ค้นหาเมนูอาหารตามชื่อเมนู หรือหมวดหมู่"""
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


def menu_sale_flags(data):
    """แยกหมดชั่วคราวจากเลิกขาย และไม่อนุญาตให้เมนูเลิกขายยังพร้อมขาย"""
    flags = []
    for key, default in (("is_available", 1), ("is_discontinued", 0)):
        value = data.get(key, default)
        if not isinstance(value, (str, int, bool)) or str(value) not in ("0", "1", "False", "True"):
            raise ValueError("สถานะเมนูต้องเป็น 0 หรือ 1")
        flags.append(int(value) if isinstance(value, (bool, int)) or value in ("0", "1")
                     else 1 if value == "True" else 0)
    available, discontinued = flags
    return (0 if discontinued else available), discontinued


def create_item(data):
    available, discontinued = menu_sale_flags(data)
    return run_command(
        "INSERT INTO menu_item (name, category, price, is_available, is_discontinued) "
        "VALUES (%s, %s, %s, %s, %s)",
        (data["name"], data["category"], data["price"], available, discontinued))


def update_item(item_id, data):
    available, discontinued = menu_sale_flags(data)
    return run_command(
        "UPDATE menu_item SET name=%s, category=%s, price=%s, "
        "is_available=%s, is_discontinued=%s WHERE item_id=%s",
        (data["name"], data["category"], data["price"], available, discontinued, item_id))


def delete_item(item_id):
    """ข้อกำหนดห้ามลบเมนู: เส้นทาง DELETE เดิมจึงเปลี่ยนเป็นเลิกขายแทน"""
    # เก็บแถวเมนูและ FK ทั้งหมดไว้ เพื่อรักษาประวัติการสั่งและส่วนประกอบคอมโบ
    return run_command(
        "UPDATE menu_item SET is_available=0, is_discontinued=1 WHERE item_id=%s",
        (item_id,))


# ---------- ชุดคอมโบ (combo) ----------
def search_combos(filters):
    """ค้นหาส่วนประกอบของชุดคอมโบตามรหัสหรือชื่อเมนู"""
    sql = """SELECT c.item_id, combo_item.name AS combo_name,
                    c.sub_item_id, sub_item.name AS sub_item_name,
                    c.amount, c.price AS combo_price
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


# ---------- รายงาน: แต่ละฟังก์ชันคืนค่าเป็น list ของ dict (ชื่อคอลัมน์ = หัวตารางบนเว็บ) ----------
def get_combo(item_id, sub_item_id):
    """ดึงส่วนประกอบ 1 รายการจากชุดคอมโบ"""
    sql = ("SELECT item_id, sub_item_id, amount, price FROM combo "
           "WHERE item_id = %s AND sub_item_id = %s")
    rows = run_query(sql, (item_id, sub_item_id))
    return rows[0] if rows else None


def create_combo(data):
    """เพิ่มเมนูย่อยลงในชุดคอมโบ — data มีคีย์: item_id, sub_item_id, amount, price"""
    # ทั้ง item_id (ชุดหลัก) และ sub_item_id (อาหารในชุด) อ้างอิง menu_item.item_id
    # ตาราง combo เป็นตารางเชื่อม: ชุดหนึ่งมีอาหารหลายอย่าง และอาหารอย่างหนึ่งอยู่ได้หลายชุด
    # schema ใช้ combo_id เป็น PK และ UNIQUE(item_id, sub_item_id) กันคู่ซ้ำ; API อ้างแถวด้วยคู่นี้
    # ราคาใน combo ไม่ถูกนำมาบวกเป็นยอดออเดอร์ ยอดสั่งชุดใช้ราคา menu_item ของชุดหลัก
    # ตรวจสอบทางธุรกิจ: เมนูหลักกับเมนูย่อยต้องไม่ใช่เมนูเดียวกัน
    if str(data.get("item_id")) == str(data.get("sub_item_id")):
        raise ValueError("เมนูชุดหลักและเมนูในชุดต้องไม่เป็นเมนูเดียวกัน")
    try:
        # ถ้าไม่ได้กรอกราคา ให้ใช้ 0.00 แทน เพื่อกันค่า NULL
        price = data.get("price") or 0.00
        sql = ("INSERT INTO combo (item_id, sub_item_id, amount, price) "
               "VALUES (%s, %s, %s, %s)")
        params = (data["item_id"], data["sub_item_id"], data["amount"], price)
        return run_command(sql, params)
    except mysql.connector.Error as err:
        # errno 1062 = Duplicate entry (คีย์ซ้ำ) → แปลเป็นข้อความไทยให้ผู้ใช้อ่านรู้เรื่อง
        if err.errno == 1062:
            raise ValueError("มีเมนูย่อยนี้ในชุดคอมโบอยู่แล้ว")
        raise


def update_combo(item_id, sub_item_id, data):
    """แก้จำนวนเมนูย่อยและราคาในชุดคอมโบ"""
    price = data.get("price") or 0.00
    sql = ("UPDATE combo SET amount = %s, price = %s "
           "WHERE item_id = %s AND sub_item_id = %s")
    params = (data["amount"], price, item_id, sub_item_id)
    return run_command(sql, params)


def delete_combo(item_id, sub_item_id):
    """ลบเมนูย่อยออกจากชุดคอมโบ"""
    sql = "DELETE FROM combo WHERE item_id = %s AND sub_item_id = %s"
    return run_command(sql, (item_id, sub_item_id))


# ---------- ออเดอร์ (food_order) ----------
def search_orders(filters):
    # ซ่อนแถวเมื่อใบเสร็จของการชำระปัจจุบันถูกลบ; ไม่ลบออเดอร์จริงหรือเปลี่ยนยอดรายงาน
    # ออเดอร์ที่ยังไม่จ่าย และออเดอร์ที่รับชำระใหม่แล้ว ยังแสดงตามปกติ
    # ยอดรวมคำนวณจาก unit_price (ราคาตอนสั่งจริง) ไม่ใช่ราคาเมนูปัจจุบัน
    sql = """SELECT o.order_id, o.cust_id, c.name AS customer_name,
                    o.table_id, t.zone, t.seats, o.order_time, o.status,
                    IFNULL(order_totals.total, 0) AS total,
                    CASE WHEN p.payment_id IS NULL THEN 'UNPAID' ELSE 'PAID' END AS payment_status,
                    CASE WHEN p.receipt_deleted_at IS NULL THEN p.payment_id ELSE NULL END AS receipt_id
             FROM food_order o
             JOIN customer c ON o.cust_id = c.cust_id
             JOIN dining_table t ON t.table_id=o.table_id
             LEFT JOIN payment p ON p.order_id=o.order_id AND p.status='PAID'
             LEFT JOIN (SELECT oi.order_id, SUM(oi.qty * oi.unit_price) AS total
                        FROM order_item oi
                        GROUP BY oi.order_id) AS order_totals
                    ON o.order_id = order_totals.order_id
             WHERE p.receipt_deleted_at IS NULL"""
    params = []

    if filters.get("cust_id"):
        sql += " AND o.cust_id = %s"
        params.append(filters["cust_id"])

    if filters.get("table_id"):
        sql += " AND o.table_id = %s"
        params.append(filters["table_id"])

    if filters.get("status"):
        sql += " AND o.status = %s"
        params.append(normalize_order_status(filters["status"]))

    if filters.get("zone"):
        if filters["zone"] not in ("INDOOR", "OUTDOOR", "VIP"):
            raise ValueError("โซนที่นั่งไม่ถูกต้อง")
        sql += " AND t.zone=%s"
        params.append(filters["zone"])
    sql += " ORDER BY o.order_time ASC, o.order_id ASC"
    # ASC เรียงออเดอร์จากเวลาเก่าไปใหม่ ถ้าเวลาเท่ากันใช้ order_id เพื่อให้ลำดับแน่นอน
    return run_query(sql, params)


def get_order(order_id):
    """ดึงออเดอร์ 1 รายการตาม order_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    sql = "SELECT o.*, t.zone, t.seats FROM food_order o JOIN dining_table t ON t.table_id=o.table_id WHERE o.order_id=%s"
    rows = run_query(sql, (order_id,))
    if not rows:
        return None
    order = rows[0]
    # food_order เก็บหัวใบสั่ง ส่วน order_item เก็บอาหารในใบสั่งนั้น เชื่อมกันด้วย order_id
    # JOIN menu_item เพื่อได้ชื่อเมนูสำหรับเติมฟอร์มแก้ไข แต่ยังใช้ราคาตอนสั่งจาก order_item
    order["items"] = run_query(
        "SELECT oi.item_id, m.name, oi.qty, oi.unit_price, oi.note "
        "FROM order_item oi JOIN menu_item m ON m.item_id = oi.item_id "
        "WHERE oi.order_id = %s ORDER BY oi.item_id", (order_id,))
    return order


# ตรวจโต๊ะก่อนใช้งาน: ออเดอร์ที่ยังไม่จ่ายจะกันโต๊ะไว้; ไม่นับออเดอร์ที่กำลังแก้ไขเอง
def check_table_free(table_id, order_id=None):
    if not run_query("SELECT table_id FROM dining_table WHERE table_id=%s", (table_id,)):
        raise ValueError("ไม่พบโต๊ะ")
    rows = run_query(
        "SELECT o.order_id FROM food_order o LEFT JOIN payment p ON p.order_id=o.order_id AND p.status='PAID' "
        "WHERE o.table_id=%s AND o.status<>'CANCELLED' AND p.payment_id IS NULL "
        "AND (o.status<>'COMPLETED' OR NOT EXISTS (SELECT 1 FROM payment ph WHERE ph.order_id=o.order_id)) "
        "AND o.order_id<>%s", (table_id, order_id or 0))
    if rows:
        raise ValueError("โต๊ะยังมีออเดอร์หรือบิลที่ยังไม่ชำระ")


def create_order(data):
    return save_order(data)


def update_order(order_id, data):
    return save_order(data, order_id)


def normalize_order_status(value):
    # รับรหัสอังกฤษตาม ENUM และรองรับข้อความไทยจากหน้าเว็บรุ่นเดิมด้วย
    # ค่าที่คืนออกไปบันทึกต้องเป็นอังกฤษเสมอ จึงไม่เกิด Data truncated สำหรับสถานะไทย
    if not isinstance(value, str):
        raise ValueError("กรุณาเลือกสถานะออเดอร์ที่ถูกต้อง")
    aliases = {"รอดำเนินการ": "PENDING", "กำลังดำเนินการ": "IN_PROGRESS",
               "พร้อมเสิร์ฟ": "READY", "เสร็จสิ้น": "COMPLETED", "ยกเลิก": "CANCELLED"}
    status = aliases.get(value, value)
    if status not in ("PENDING", "IN_PROGRESS", "READY", "COMPLETED", "CANCELLED"):
        raise ValueError("กรุณาเลือกสถานะออเดอร์ที่ถูกต้อง")
    return status


def positive_integer(value, label):
    # ตรวจที่เซิร์ฟเวอร์ด้วย เพราะผู้ใช้สามารถเรียก API โดยไม่ผ่านการตรวจของหน้าเว็บได้
    if isinstance(value, bool) or not str(value).isdigit():
        raise ValueError(f"{label}ต้องเป็นจำนวนเต็มมากกว่า 0")
    number = int(value)
    if not 1 <= number <= 2147483647:
        raise ValueError(f"{label}ต้องเป็นจำนวนเต็มมากกว่า 0 และไม่เกิน 2147483647")
    return number


# เกณฑ์ที่ร้านกำหนด: ยอดซื้อสะสมจากออเดอร์ COMPLETED เท่านั้น
# Regular: ต่ำกว่า 3,000 / Gold: ตั้งแต่ 3,000 / VIP: ตั้งแต่ 10,000 บาท
# เป็นสิทธิ์ที่เลื่อนขึ้นอย่างเดียว: แก้ไข/ยกเลิกออเดอร์ภายหลังไม่ลดระดับเดิม
MEMBER_TIERS = ("Regular", "Gold", "VIP")


# รวมยอดอาหารของลูกค้าจากออเดอร์เสร็จสิ้น แล้วเลื่อนระดับเฉพาะเมื่อสูงกว่าระดับปัจจุบัน
def promote_member(cur, cust_id, current_tier):
    # อ่านราคาตอนสั่งจริง และใช้ locking read เพื่อเห็นรายการล่าสุดในธุรกรรมนี้
    cur.execute(
        "SELECT oi.qty, oi.unit_price FROM food_order o "
        "JOIN order_item oi ON oi.order_id=o.order_id "
        "WHERE o.cust_id=%s AND o.status='COMPLETED' FOR UPDATE", (cust_id,))
    total = sum((Decimal(str(row["unit_price"])) * row["qty"]
                 for row in cur.fetchall()), Decimal("0"))
    earned = "VIP" if total >= 10000 else "Gold" if total >= 3000 else "Regular"
    if MEMBER_TIERS.index(earned) > MEMBER_TIERS.index(current_tier):
        cur.execute("UPDATE customer SET member_tier=%s WHERE cust_id=%s", (earned, cust_id))


def save_order(data, order_id=None):
    """บันทึกใบออเดอร์และรายการอาหารในธุรกรรมเดียว ราคามาจากฐานข้อมูลเท่านั้น"""
    # ใช้ฟังก์ชันเดียวกันสำหรับเพิ่มและแก้ไข เพื่อตรวจข้อมูลและคิดราคาด้วยหลักเดียวกัน
    if not isinstance(data, dict):
        raise ValueError("ข้อมูลออเดอร์ไม่ถูกต้อง")
    status = normalize_order_status(data.get("status", "PENDING"))
    cust_id = positive_integer(data.get("cust_id"), "รหัสลูกค้า")
    table_id = positive_integer(data.get("table_id"), "รหัสโต๊ะ")
    order_time = blank_to_none(data.get("order_time"))
    if order_time is not None:
        try:
            order_time = datetime.fromisoformat(str(order_time))
            if order_time.tzinfo is not None:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("กรุณาระบุเวลาสั่งให้ถูกต้อง") from None

    items = data.get("items")
    parsed = []
    if "items" in data:
        if not isinstance(items, list) or not items:
            raise ValueError("กรุณาเลือกเมนูอาหารอย่างน้อย 1 รายการ")
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("รายการอาหารไม่ถูกต้อง")
            item_id = positive_integer(item.get("item_id"), "รหัสเมนู")
            qty = positive_integer(item.get("qty"), "จำนวนอาหาร")
            if item_id in seen:
                raise ValueError("เมนูซ้ำกัน กรุณารวมจำนวนในรายการเดียว")
            seen.add(item_id)
            note = item.get("note") or ""
            if not isinstance(note, str) or len(note) > 255:
                raise ValueError("หมายเหตุอาหารต้องไม่เกิน 255 ตัวอักษร")
            parsed.append((item_id, qty, note))

    conn = get_connection()
    cur = None
    try:
        conn.start_transaction()
        # ทุกคำสั่งของการบันทึกนี้ใช้ connection เดียวกัน จึง commit หรือ rollback พร้อมกันได้
        cur = conn.cursor(dictionary=True)
        existing = {}
        if order_id is not None:
            # FOR UPDATE ล็อกออเดอร์ระหว่างทำรายการ ป้องกันการแก้ไขพร้อมกัน
            cur.execute("SELECT order_id FROM food_order WHERE order_id = %s FOR UPDATE", (order_id,))
            if not cur.fetchone():
                raise ValueError("ไม่พบออเดอร์นี้")
            cur.execute("SELECT payment_id FROM payment WHERE order_id=%s AND status='PAID' LIMIT 1", (order_id,))
            if cur.fetchone():
                raise ValueError("ออเดอร์ชำระเงินแล้ว ไม่สามารถแก้ไขได้")
            cur.execute("SELECT item_id, qty, unit_price FROM order_item WHERE order_id = %s", (order_id,))
            existing = {row["item_id"]: row for row in cur.fetchall()}

        # ล็อกแถวโต๊ะ เพื่อให้การเปิดออเดอร์พร้อมกันตรวจโต๊ะว่างภายใต้ธุรกรรมเดียว
        cur.execute("SELECT table_id, zone FROM dining_table WHERE table_id = %s FOR UPDATE", (table_id,))
        table = cur.fetchone()
        if not table:
            raise ValueError(f"โต๊ะ {table_id} ไม่มีอยู่จริง")
        # zone เป็นตัวช่วยเลือกโต๊ะ ไม่เก็บซ้ำใน food_order; ใช้โซนจริงจาก dining_table
        if data.get("zone") and data["zone"] != table["zone"]:
            raise ValueError("โต๊ะที่เลือกไม่อยู่ในโซนที่ระบุ กรุณาเลือกโต๊ะใหม่")
        # ล็อกลูกค้าเพื่อให้การเลื่อนระดับจากออเดอร์พร้อมกันไม่ทับกัน
        cur.execute("SELECT cust_id, member_tier FROM customer WHERE cust_id = %s FOR UPDATE", (cust_id,))
        customer = cur.fetchone()
        if not customer:
            raise ValueError("ไม่พบลูกค้าที่เลือก")
        # ตรวจซ้ำที่เซิร์ฟเวอร์ แม้หน้าเว็บแสดงโต๊ะว่าง เพราะอาจมีคนอื่นเลือกโต๊ะไปแล้ว
        if status != "CANCELLED":
            cur.execute(
                "SELECT o.order_id FROM food_order o LEFT JOIN payment p ON p.order_id=o.order_id AND p.status='PAID' "
                "WHERE o.table_id=%s AND o.status<>'CANCELLED' AND p.payment_id IS NULL "
                "AND (o.status<>'COMPLETED' OR NOT EXISTS (SELECT 1 FROM payment ph WHERE ph.order_id=o.order_id)) "
                "AND o.order_id<>%s LIMIT 1 FOR UPDATE", (table_id, order_id or 0))
            if cur.fetchone():
                raise ValueError(f"โต๊ะ {table_id} ยังมีออเดอร์หรือบิลที่ยังไม่ชำระ")

        lines = []
        # อ่านราคาและสถานะพร้อมขายจากฐานข้อมูลจริง ไม่เชื่อราคาที่อาจถูกแก้จากเบราว์เซอร์
        # เมนูชุดคอมโบก็เป็น menu_item หนึ่งรายการ จึงสั่งได้ด้วยขั้นตอนเดียวกับเมนูทั่วไป
        for item_id, qty, note in sorted(parsed):
            cur.execute(
                "SELECT item_id, name, price, is_available, is_discontinued "
                "FROM menu_item WHERE item_id = %s FOR UPDATE", (item_id,))
            menu = cur.fetchone()
            if not menu:
                raise ValueError("ไม่พบเมนูที่เลือก")
            old = existing.get(item_id)
            available = bool(menu["is_available"]) and not bool(menu["is_discontinued"])
            if not available and (old is None or qty > old["qty"]):
                raise ValueError(f"เมนู {menu['name']} ไม่พร้อมขาย")
            price = old["unit_price"] if old else menu["price"]
            # รายการเดิมคงราคาตอนสั่ง ส่วนรายการที่เพิ่มใหม่ใช้ราคาปัจจุบัน
            lines.append((item_id, qty, price, note))

        if order_id is None:
            cur.execute(
                "INSERT INTO food_order (cust_id, table_id, order_time, status) "
                "VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s)",
                (cust_id, table_id, order_time, status))
            order_id = cur.lastrowid
            new_id = order_id
        else:
            cur.execute(
                "UPDATE food_order SET cust_id=%s, table_id=%s, "
                "order_time=COALESCE(%s, order_time), status=%s WHERE order_id=%s",
                (cust_id, table_id, order_time, status, order_id))
            new_id = None
        # ลูกค้า API เดิมที่ไม่ได้ส่ง items ยังสามารถแก้สถานะโดยคงรายการอาหารเดิม
        if items is not None:
            # ถ้าส่งรายการอาหารมา ให้แทนรายการเดิมด้วยชุดล่าสุดภายใต้ธุรกรรมเดียว
            # order_item เก็บ qty และ unit_price เพื่อให้รายงานคำนวณ SUM(qty * unit_price) ได้
            # ลบเฉพาะรายการอาหารของออเดอร์นี้ก่อนใส่ชุดใหม่ ไม่ได้ลบหัวออเดอร์
            cur.execute("DELETE FROM order_item WHERE order_id = %s", (order_id,))
            for item_id, qty, price, note in lines:
                cur.execute(
                    "INSERT INTO order_item (order_id, item_id, qty, unit_price, note) "
                    "VALUES (%s, %s, %s, %s, %s)", (order_id, item_id, qty, price, note))
        # เลื่อนระดับพร้อมกับบันทึกออเดอร์: ถ้าส่วนใดผิดพลาด rollback ทั้งหมด
        promote_member(cur, cust_id, customer["member_tier"])
        # commit ยืนยันหัวออเดอร์ รายการอาหาร และระดับสมาชิกพร้อมกัน เมื่อทุกขั้นตอนสำเร็จ
        conn.commit()
        return {"new_id": new_id, "affected": 1, "order_id": order_id}
    except Exception:
        # ถ้าบันทึกส่วนใดล้มเหลว ให้ยกเลิกทั้งหมด เพื่อไม่ให้เหลือใบออเดอร์ที่อาหารบันทึกไม่ครบ
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close()
        conn.close()


def delete_order(order_id):
    """ลบภายใต้ธุรกรรมเดียว; บิลจ่ายแล้วหรือมีรีวิวต้องคงประวัติไว้"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT order_id FROM food_order WHERE order_id=%s FOR UPDATE", (order_id,))
        if not cur.fetchone():
            raise ValueError("ไม่พบออเดอร์")
        # มีประวัติรับเงินแล้วห้ามลบออเดอร์ แม้ซ่อนใบเสร็จไปแล้ว เพื่อให้รายงานยังอ้างอิงได้
        cur.execute("SELECT payment_id FROM payment WHERE order_id=%s LIMIT 1", (order_id,))
        if cur.fetchone():
            raise ValueError("ออเดอร์มีประวัติการชำระเงิน จึงไม่สามารถลบได้")
        cur.execute("SELECT review_id FROM review WHERE order_id=%s LIMIT 1", (order_id,))
        if cur.fetchone():
            raise ValueError("ออเดอร์มีรีวิวแล้ว จึงต้องเก็บประวัติไว้")
        cur.execute("DELETE FROM order_item WHERE order_id=%s", (order_id,))
        cur.execute("DELETE FROM food_order WHERE order_id=%s", (order_id,))
        conn.commit()
        return {"affected": 1}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ---------- รีวิวร้านอาหาร (review) ----------
def search_reviews(filters):
    """ค้นหารีวิวร้านอาหารตาม rating หรือ ข้อความ"""
    sql = """SELECT r.review_id, r.cust_id, c.name AS customer_name,
                    r.order_id, r.rating, r.comment, r.review_time
             FROM review r
             JOIN customer c ON r.cust_id = c.cust_id
             WHERE 1=1"""
    params = []

    if filters.get("rating"):
        sql += " AND r.rating = %s"
        params.append(filters["rating"])

    if filters.get("comment"):
        sql += " AND r.comment LIKE %s"
        params.append("%" + filters["comment"] + "%")

    sql += " ORDER BY r.review_time DESC"
    return run_query(sql, params)


def get_review(review_id):
    """ดึงข้อมูลรีวิว 1 รายการ"""
    sql = "SELECT * FROM review WHERE review_id = %s"
    rows = run_query(sql, (review_id,))
    return rows[0] if rows else None


def create_review(data):
    from restaurant_ops import save_review
    return save_review(data)


def update_review(review_id, data):
    from restaurant_ops import save_review
    return save_review(data, review_id)


def delete_review(review_id):
    """ลบรีวิว"""
    sql = "DELETE FROM review WHERE review_id=%s"
    return run_command(sql, (review_id,))


# ============================================================
#  REPORT (รายงาน — ใช้ JOIN + GROUP BY + subquery)
#  ★ ชื่อคอลัมน์ใน SELECT จะกลายเป็นหัวตารางบนเว็บ — ใช้ AS 'ชื่อภาษาไทย' ได้
# ============================================================
# ยอดขายและเมนูขายดีนับเฉพาะ COMPLETED; จำนวนออเดอร์บนการ์ดยังคงนับทุกสถานะ
def report_summary():
    """🔢 การ์ดสรุปตัวเลขบน Dashboard — ใช้ subquery นับ/รวมค่าจากแต่ละตารางแล้วคืนเป็นคอลัมน์
    (MySQL จะใช้ชื่อ alias ภาษาไทยเป็นคีย์ของ dict → 1 คีย์ = 1 การ์ดบนหน้า /report)"""
    sql = """SELECT
                (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
                (SELECT COUNT(*) FROM menu_item) AS 'เมนู',
                (SELECT COUNT(*) FROM food_order) AS 'ออเดอร์',
                (SELECT IFNULL(SUM(oi.qty * oi.unit_price), 0)
                 FROM order_item oi JOIN food_order o ON o.order_id=oi.order_id
                 WHERE o.status='COMPLETED') AS 'มูลค่าอาหารก่อนส่วนลด',
                (SELECT IFNULL(SUM(total),0) FROM payment WHERE status='PAID') AS 'รับเงินจริงหลังส่วนลด',
                (SELECT COUNT(*) FROM dining_table) AS 'โต๊ะทั้งหมด',
                (SELECT COUNT(*) FROM menu_item WHERE is_available = 1) AS 'เมนูที่พร้อมขาย',
                (SELECT COUNT(*) FROM review) AS 'จำนวนรีวิว',
                (SELECT IFNULL(ROUND(AVG(rating), 1), 0) FROM review) AS 'คะแนนรีวิวเฉลี่ย'
            """
    return run_query(sql)[0]


def report_popular_items():
    """📈 เมนูขายดี (Best Sellers)"""
    # JOIN order_item กับ menu_item เพื่อเอากลุบเมนูย่อยเป็นรายเมนู แล้วเรียงจากขายได้มากสุด → เอา 5 อันดับ
    sql = """SELECT mi.name AS 'เมนู', SUM(oi.qty) AS 'จำนวนขาย'
             FROM order_item oi
             INNER JOIN menu_item mi ON oi.item_id = mi.item_id
             INNER JOIN food_order o ON o.order_id = oi.order_id
             WHERE o.status='COMPLETED'
             GROUP BY mi.item_id, mi.name
             ORDER BY SUM(oi.qty) DESC
             LIMIT 5"""
    return run_query(sql)


# รายงานนี้รวม qty × unit_price ตามวันที่สั่ง เป็นยอดก่อนส่วนลด ไม่ใช่ยอดรับเงินจริง
def report_daily_sales():
    """💰 มูลค่าอาหารก่อนส่วนลดต่อวัน"""
    sql = """SELECT DATE(o.order_time) AS 'วันที่',
                    IFNULL(SUM(oi.qty * oi.unit_price), 0) AS 'ยอดขายรวม'
             FROM food_order o
             INNER JOIN order_item oi ON o.order_id = oi.order_id
             WHERE o.status='COMPLETED'
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
             WHERE o.status='COMPLETED'
             GROUP BY o.order_id, c.name
             HAVING SUM(oi.qty * oi.unit_price) > 500
             ORDER BY SUM(oi.qty * oi.unit_price) DESC"""
    return run_query(sql)


def report_sales_by_category():
    """📊 ยอดขายแยกตามหมวดหมู่ (Sales by Category)
    - COUNT(DISTINCT mi.item_id) นับเมนูไม่ซ้ำในหมวดนั้น
    - GROUP BY mi.category รวมกลุ่มตามหมวดหมู่ (ไม่ให้ซ้ำ) แล้วเรียงตามยอดขาย"""
    sql = """SELECT mi.category AS 'หมวดหมู่',
                    COUNT(DISTINCT mi.item_id) AS 'จำนวนเมนู',
                    SUM(oi.qty) AS 'จำนวนจานที่ขายได้',
                    IFNULL(SUM(oi.qty * oi.unit_price), 0) AS 'ยอดขายรวม'
             FROM menu_item mi
             INNER JOIN order_item oi ON mi.item_id = oi.item_id
             INNER JOIN food_order o ON o.order_id = oi.order_id
             WHERE o.status='COMPLETED'
             GROUP BY mi.category
             ORDER BY SUM(oi.qty * oi.unit_price) DESC"""
    return run_query(sql)


def report_top_customers():
    """👑 ลูกค้าที่มียอดใช้จ่ายสูงสุด (Top Spenders)"""
    sql = """SELECT c.cust_id AS 'รหัสลูกค้า',
                    c.name AS 'ชื่อลูกค้า',
                    c.member_tier AS 'ระดับสมาชิก',
                    COUNT(DISTINCT o.order_id) AS 'จำนวนออเดอร์',
                    IFNULL(SUM(oi.qty * oi.unit_price), 0) AS 'ยอดใช้จ่ายรวม'
             FROM customer c
             INNER JOIN food_order o ON c.cust_id = o.cust_id
             INNER JOIN order_item oi ON o.order_id = oi.order_id
             WHERE o.status='COMPLETED'
             GROUP BY c.cust_id, c.name, c.member_tier
             ORDER BY SUM(oi.qty * oi.unit_price) DESC"""
    return run_query(sql)


def report_reviews_summary():
    """⭐ สรุปคะแนนรีวิวและความคิดเห็นของลูกค้า (Customer Reviews)
    - CONCAT + REPEAT('⭐', rating) วาดรูปดาวตามคะแนน เช่น 3 → ⭐⭐⭐ (3/5)"""
    sql = """SELECT r.review_id AS 'รหัสรีวิว',
                    c.name AS 'ลูกค้า',
                    CONCAT(REPEAT('⭐', r.rating), ' (', r.rating, '/5)') AS 'คะแนน',
                    r.comment AS 'ความคิดเห็น',
                    r.review_time AS 'เวลารีวิว'
             FROM review r
             JOIN customer c ON r.cust_id = c.cust_id
             ORDER BY r.review_time DESC"""
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
    ("popular-items",      "📈 เมนูขายดี (Best Sellers)",                  report_popular_items),
    ("daily-sales",        "💰 มูลค่าอาหารก่อนส่วนลดต่อวัน",             report_daily_sales),
    ("big-orders",         "🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)",           report_big_orders),
    ("sales-by-category",  "📊 ยอดขายแยกตามหมวดหมู่ (Sales by Category)",   report_sales_by_category),
    ("top-customers",      "👑 ลูกค้าที่มียอดใช้จ่ายสูงสุด (Top Spenders)",  report_top_customers),
    ("reviews",            "⭐ สรุปคะแนนรีวิวและความคิดเห็น (Reviews)",     report_reviews_summary),
]


def report_received_daily():
    """เงินที่รับจริงตามวันที่จ่าย ต่างจากมูลค่าอาหารที่เสิร์ฟตามวันที่สั่ง"""
    return run_query("""SELECT DATE(payment_time) AS 'วันที่รับเงิน',
        COUNT(*) AS 'จำนวนบิล', SUM(subtotal) AS 'ก่อนส่วนลด',
        SUM(discount_amount) AS 'ส่วนลด', SUM(total) AS 'รับเงินจริง'
        FROM payment WHERE status='PAID' GROUP BY DATE(payment_time) ORDER BY DATE(payment_time)""")


REPORTS.append(("received-daily", "ยอดรับเงินจริงหลังส่วนลดต่อวัน", report_received_daily))


# รายการโต๊ะสำหรับฟอร์ม: occupied=0 คือว่าง, occupied=1 คือมีออเดอร์ค้าง
# ใช้ payment สถานะ PAID ตรวจการจ่ายเงิน ไม่ใช้การมี/ไม่มีใบเสร็จที่แสดงบนหน้าเว็บ
def list_dining_tables(filters):
    """ตัวเลือกโต๊ะตามโซน พร้อมสถานะใช้งาน ไม่สร้างหน้าจัดการโต๊ะแยก"""
    exclude = positive_integer(filters["exclude_order_id"], "รหัสออเดอร์") if filters.get("exclude_order_id") else 0
    return run_query("""SELECT t.table_id, t.zone, t.seats,
        CASE WHEN EXISTS(SELECT 1 FROM food_order o LEFT JOIN payment p ON p.order_id=o.order_id AND p.status='PAID'
            WHERE o.table_id=t.table_id AND o.status<>'CANCELLED' AND p.payment_id IS NULL
            AND (o.status<>'COMPLETED' OR NOT EXISTS (SELECT 1 FROM payment ph WHERE ph.order_id=o.order_id))
            AND o.order_id<>%s) THEN 1 ELSE 0 END AS occupied
        FROM dining_table t ORDER BY t.table_id""", (exclude,))
