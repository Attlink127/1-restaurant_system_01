# ============================================================
#  db.py — ชั้นติดต่อฐานข้อมูล
#  ใช้ %s เป็น placeholder เสมอ (กัน SQL injection)
# ============================================================
import mysql.connector
import config
from datetime import datetime

# สถานะออเดอร์ที่ถือว่า "ยังใช้โต๊ะอยู่" (ตรงกับ ENUM ใน schema.sql)
ACTIVE_STATUSES = ("PENDING", "IN_PROGRESS")


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
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ()); rows = cur.fetchall()
    cur.close(); conn.close(); return rows


def run_command(sql, params=None):
    """รันคำสั่งที่เปลี่ยนแปลงข้อมูล (INSERT / UPDATE / DELETE) แล้ว commit
    - ต้อง commit() ไม่งั้นข้อมูลจะไม่ถูกบันทึกจริงลงฐานข้อมูล
    - คืนค่า new_id (id ที่เพิ่ง insert ล่าสุด) และ affected (จำนวนแถวที่ถูกแก้/ลบ)
      เพื่อให้ฝั่งเว็บรู้ว่าทำงานสำเร็จ"""
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
    """ดึงลูกค้า 1 รายตาม cust_id (คืน dict แถวเดียว หรือ None ถ้าไม่พบ)"""
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
    try:
        sql = "DELETE FROM menu_item WHERE item_id=%s"
        return run_command(sql, (item_id,))
    except mysql.connector.Error as err:
        if err.errno == 1451:
            raise ValueError("ไม่สามารถลบเมนูนี้ได้ เนื่องจากมีประวัติการสั่งซื้อหรืออยู่ในชุดคอมโบ (แนะนำให้แก้ไขโดยปิด 'พร้อมขาย' แทน)")
        raise


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
    # combo_id เป็น PRIMARY KEY ส่วนคู่ (item_id, sub_item_id) มี UNIQUE เพื่อไม่ให้อาหารซ้ำในชุด
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
        params.append(normalize_order_status(filters["status"]))

    sql += " ORDER BY o.order_time ASC, o.order_id ASC"
    # ASC เรียงออเดอร์จากเวลาเก่าไปใหม่ ถ้าเวลาเท่ากันใช้ order_id เพื่อให้ลำดับแน่นอน
    return run_query(sql, params)


def get_order(order_id):
    """ดึงออเดอร์ 1 รายการตาม order_id (ใช้ตอนเปิดฟอร์มแก้ไข)"""
    sql = "SELECT * FROM food_order WHERE order_id = %s"
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
    return save_order(data)


def update_order(order_id, data):
    return save_order(data, order_id)


def normalize_order_status(value):
    # รับรหัสอังกฤษตาม ENUM และรองรับข้อความไทยจากหน้าเว็บรุ่นเดิมด้วย
    # ค่าที่คืนออกไปบันทึกต้องเป็นอังกฤษเสมอ จึงไม่เกิด Data truncated สำหรับสถานะไทย
    if not isinstance(value, str):
        raise ValueError("กรุณาเลือกสถานะออเดอร์ที่ถูกต้อง")
    aliases = {"รอดำเนินการ": "PENDING", "กำลังดำเนินการ": "IN_PROGRESS",
               "เสร็จสิ้น": "COMPLETED", "ยกเลิก": "CANCELLED"}
    status = aliases.get(value, value)
    if status not in ("PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"):
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
            cur.execute("SELECT order_id FROM food_order WHERE order_id = %s FOR UPDATE", (order_id,))
            if not cur.fetchone():
                raise ValueError("ไม่พบออเดอร์นี้")
            cur.execute("SELECT item_id, qty, unit_price FROM order_item WHERE order_id = %s", (order_id,))
            existing = {row["item_id"]: row for row in cur.fetchall()}

        # ล็อกแถวโต๊ะ เพื่อให้การเปิดออเดอร์พร้อมกันตรวจโต๊ะว่างภายใต้ธุรกรรมเดียว
        cur.execute("SELECT table_id FROM dining_table WHERE table_id = %s FOR UPDATE", (table_id,))
        if not cur.fetchone():
            raise ValueError(f"โต๊ะ {table_id} ไม่มีอยู่จริง")
        cur.execute("SELECT cust_id FROM customer WHERE cust_id = %s", (cust_id,))
        if not cur.fetchone():
            raise ValueError("ไม่พบลูกค้าที่เลือก")
        if status in ACTIVE_STATUSES:
            cur.execute(
                "SELECT order_id FROM food_order WHERE table_id = %s "
                "AND status IN ('PENDING', 'IN_PROGRESS') AND order_id <> %s",
                (table_id, order_id or 0))
            if cur.fetchone():
                raise ValueError(f"โต๊ะ {table_id} ยังมีออเดอร์ที่ยังไม่เสร็จสิ้น")

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
            cur.execute("DELETE FROM order_item WHERE order_id = %s", (order_id,))
            for item_id, qty, price, note in lines:
                cur.execute(
                    "INSERT INTO order_item (order_id, item_id, qty, unit_price, note) "
                    "VALUES (%s, %s, %s, %s, %s)", (order_id, item_id, qty, price, note))
        conn.commit()
        # ถึงจุดนี้ใบออเดอร์และอาหารทุกแถวถูกบันทึกสำเร็จแล้ว จึงยืนยันทั้งหมดพร้อมกัน
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
    """ลบออเดอร์และรายการอาหารในออเดอร์"""
    run_command("DELETE FROM order_item WHERE order_id=%s", (order_id,))
    sql = "DELETE FROM food_order WHERE order_id=%s"
    return run_command(sql, (order_id,))


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
    """เพิ่มรีวิวใหม่"""
    rating = int(data.get("rating", 5))
    if not (1 <= rating <= 5):
        raise ValueError("คะแนนรีวิวต้องอยู่ระหว่าง 1 ถึง 5 ดาว")
    sql = ("INSERT INTO review (cust_id, order_id, rating, comment, review_time) "
           "VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)")
    params = (data["cust_id"], blank_to_none(data.get("order_id")),
              rating, data.get("comment", ""))
    return run_command(sql, params)


def update_review(review_id, data):
    """แก้ไขรีวิว"""
    rating = int(data.get("rating", 5))
    if not (1 <= rating <= 5):
        raise ValueError("คะแนนรีวิวต้องอยู่ระหว่าง 1 ถึง 5 ดาว")
    sql = ("UPDATE review SET cust_id=%s, order_id=%s, rating=%s, comment=%s "
           "WHERE review_id=%s")
    params = (data["cust_id"], blank_to_none(data.get("order_id")),
              rating, data.get("comment", ""), review_id)
    return run_command(sql, params)


def delete_review(review_id):
    """ลบรีวิว"""
    sql = "DELETE FROM review WHERE review_id=%s"
    return run_command(sql, (review_id,))


# ============================================================
#  REPORT (รายงาน — ใช้ JOIN + GROUP BY + subquery)
#  ★ ชื่อคอลัมน์ใน SELECT จะกลายเป็นหัวตารางบนเว็บ — ใช้ AS 'ชื่อภาษาไทย' ได้
# ============================================================
def report_summary():
    """🔢 การ์ดสรุปตัวเลขบน Dashboard — ใช้ subquery นับ/รวมค่าจากแต่ละตารางแล้วคืนเป็นคอลัมน์
    (MySQL จะใช้ชื่อ alias ภาษาไทยเป็นคีย์ของ dict → 1 คีย์ = 1 การ์ดบนหน้า /report)"""
    sql = """SELECT
                (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
                (SELECT COUNT(*) FROM menu_item) AS 'เมนู',
                (SELECT COUNT(*) FROM food_order) AS 'ออเดอร์',
                (SELECT IFNULL(SUM(qty * unit_price), 0)
                 FROM order_item) AS 'ยอดขายรวม',
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
    ("daily-sales",        "💰 ยอดขายรวมต่อวัน (Daily Sales)",             report_daily_sales),
    ("big-orders",         "🧾 ออเดอร์ยอดเกิน 500 บาท (HAVING)",           report_big_orders),
    ("sales-by-category",  "📊 ยอดขายแยกตามหมวดหมู่ (Sales by Category)",   report_sales_by_category),
    ("top-customers",      "👑 ลูกค้าที่มียอดใช้จ่ายสูงสุด (Top Spenders)",  report_top_customers),
    ("reviews",            "⭐ สรุปคะแนนรีวิวและความคิดเห็น (Reviews)",     report_reviews_summary),
]
