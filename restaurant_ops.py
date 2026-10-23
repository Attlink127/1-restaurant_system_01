"""รายละเอียดออเดอร์ → รับชำระ → ใบเสร็จ

แยกสถานะอาหารออกจากการชำระเงินจริง: COMPLETED หมายถึงเสิร์ฟแล้ว
โต๊ะยังไม่ว่างจนกว่าจะมี payment หรือออเดอร์ถูกยกเลิก
"""
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import db

DISCOUNTS = {"Regular": Decimal("0"), "Gold": Decimal("5"), "VIP": Decimal("10")}
CENT = Decimal("0.01")


def money(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number > Decimal("99999999.99"):
            raise ValueError()
        rounded = number.quantize(CENT, rounding=ROUND_HALF_UP)
        if rounded != number:
            raise ValueError()
        return rounded
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError("จำนวนเงินต้องไม่ติดลบ และมีทศนิยมไม่เกิน 2 ตำแหน่ง") from None


def bill_amounts(items, tier):
    subtotal = money(sum((Decimal(str(i["unit_price"])) * i["qty"] for i in items), Decimal(0)))
    rate = DISCOUNTS.get(tier, Decimal(0))
    discount = (subtotal * rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    return dict(subtotal=subtotal, discount_rate=rate, discount_amount=discount, total=subtotal-discount)


def order_detail(order_id):
    order = db.get_order(order_id)
    if not order:
        raise ValueError("ไม่พบออเดอร์")
    customer = db.get_customer(order["cust_id"])
    order["customer_name"] = customer["name"]
    order["member_tier"] = customer["member_tier"]
    order["bill"] = bill_amounts(order["items"], customer["member_tier"])
    # ไม่ส่ง snapshot ขนาดใหญ่ในหน้ารายการ แต่ใช้ snapshot สำหรับใบเสร็จเสมอ
    payments = db.run_query("SELECT payment_id, method, total, payment_time FROM payment WHERE order_id=%s AND status='PAID'", (order_id,))
    order["payment"] = payments[0] if payments else None
    return order


def checkout(order_id, data):
    if not isinstance(data, dict):
        raise ValueError("ข้อมูลการชำระเงินไม่ถูกต้อง")
    method = data.get("method")
    if method not in ("CASH", "TRANSFER"):
        raise ValueError("กรุณาเลือกเงินสดหรือโอนเงิน")
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        # การรับเงินและการแก้ไขออเดอร์ล็อกหัวใบสั่งเดียวกัน จึงไม่เปลี่ยนยอดระหว่างรับเงิน
        cur.execute("SELECT * FROM food_order WHERE order_id=%s FOR UPDATE", (order_id,))
        order = cur.fetchone()
        if not order or order["status"] != "COMPLETED":
            raise ValueError("ชำระเงินได้เมื่อออเดอร์เสิร์ฟครบแล้วเท่านั้น")
        cur.execute("SELECT payment_id FROM payment WHERE order_id=%s AND status='PAID'", (order_id,))
        if cur.fetchone():
            raise ValueError("ออเดอร์นี้ชำระเงินแล้ว")
        cur.execute("SELECT name, member_tier FROM customer WHERE cust_id=%s FOR UPDATE", (order["cust_id"],))
        customer = cur.fetchone()
        cur.execute("""SELECT oi.item_id, m.name, oi.qty, oi.unit_price, oi.note
            FROM order_item oi JOIN menu_item m ON m.item_id=oi.item_id
            WHERE oi.order_id=%s ORDER BY oi.item_id FOR UPDATE""", (order_id,))
        items = cur.fetchall()
        if not items:
            raise ValueError("ไม่สามารถชำระออเดอร์ที่ไม่มีรายการอาหาร")
        amounts = bill_amounts(items, customer["member_tier"])
        # ฟอร์มต้องยืนยันยอดที่เห็น ถ้ามีคนเปลี่ยนออเดอร์หรือระดับสมาชิกให้ตรวจบิลใหม่ก่อนรับเงิน
        if money(data.get("expected_total")) != amounts["total"]:
            raise ValueError("ยอดชำระเปลี่ยนแล้ว กรุณาเปิดรายละเอียดออเดอร์ใหม่")
        received = money(data.get("received"))
        if received < amounts["total"] or (method == "TRANSFER" and received != amounts["total"]):
            raise ValueError("เงินสดต้องรับให้ครบยอด และยอดโอนต้องตรงกับยอดสุทธิ")
        change = received - amounts["total"]
        # เก็บสำเนาชื่อเมนู ราคา สมาชิก และส่วนลดตอนจ่าย เพื่อให้ใบเสร็จเก่าไม่เปลี่ยนตามข้อมูลปัจจุบัน
        cur.execute("SELECT zone FROM dining_table WHERE table_id=%s", (order["table_id"],))
        table = cur.fetchone()
        snapshot = dict(order_id=order_id, table_id=order["table_id"], zone=table["zone"], customer_name=customer["name"],
                        member_tier=customer["member_tier"], items=items)
        cur.execute("""INSERT INTO payment
            (order_id, method, subtotal, member_tier, discount_rate, discount_amount, total,
             received, change_amount, receipt_snapshot)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (order_id, method, amounts["subtotal"], customer["member_tier"], amounts["discount_rate"],
             amounts["discount_amount"], amounts["total"], received, change,
             json.dumps(snapshot, ensure_ascii=False, default=str)))
        payment_id = cur.lastrowid
        conn.commit()
        return dict(payment_id=payment_id, total=amounts["total"], change_amount=change)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def receipt(payment_id):
    rows = db.run_query("SELECT * FROM payment WHERE payment_id=%s AND receipt_deleted_at IS NULL", (payment_id,))
    if not rows:
        raise ValueError("ไม่พบใบเสร็จ")
    result = rows[0]
    if isinstance(result["payment_time"], str):
        result["payment_time"] = datetime.fromisoformat(result["payment_time"])
    snapshot = result["receipt_snapshot"]
    result["snapshot"] = json.loads(snapshot) if isinstance(snapshot, str) else snapshot
    for item in result["snapshot"]["items"]:
        item["line_total"] = Decimal(str(item["unit_price"])) * item["qty"]
    return result


def search_payments(filters):
    """ค้นประวัติที่ชำระสำเร็จ โดยชื่อในใบเสร็จยึด snapshot ตอนจ่าย"""
    sql = """SELECT p.payment_id, p.order_id,
        JSON_UNQUOTE(JSON_EXTRACT(p.receipt_snapshot, '$.customer_name')) AS customer_name,
        p.member_tier, p.method, p.subtotal, p.discount_amount, p.total,
        p.received, p.change_amount, p.payment_time, p.status AS payment_state,
        p.cancel_reason, p.cancelled_at FROM payment p WHERE p.receipt_deleted_at IS NULL"""
    params = []
    if filters.get("order_id"):
        sql += " AND p.order_id=%s"
        params.append(db.positive_integer(filters["order_id"], "รหัสออเดอร์"))
    if filters.get("customer_name"):
        sql += " AND JSON_UNQUOTE(JSON_EXTRACT(p.receipt_snapshot, '$.customer_name')) LIKE %s"
        params.append('%' + filters["customer_name"] + '%')
    if filters.get("payment_date"):
        try:
            date = datetime.strptime(filters["payment_date"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError("วันที่ชำระเงินไม่ถูกต้อง") from None
        sql += " AND DATE(p.payment_time)=%s"
        params.append(date.isoformat())
    if filters.get("method"):
        if filters["method"] not in ("CASH", "TRANSFER"):
            raise ValueError("วิธีชำระเงินไม่ถูกต้อง")
        sql += " AND p.method=%s"
        params.append(filters["method"])
    if filters.get("payment_state"):
        if filters["payment_state"] not in ("PAID", "CANCELLED"):
            raise ValueError("สถานะบิลไม่ถูกต้อง")
        sql += " AND p.status=%s"
        params.append(filters["payment_state"])
    return db.run_query(sql + " ORDER BY p.payment_time DESC, p.payment_id DESC", params)


def save_review(data, review_id=None):
    cust_id = db.positive_integer(data.get("cust_id"), "รหัสลูกค้า")
    order_id = db.positive_integer(data.get("order_id"), "รหัสออเดอร์")
    rating = db.positive_integer(data.get("rating"), "คะแนน")
    comment = data.get("comment") or ""
    if rating > 5 or not isinstance(comment, str) or len(comment) > 255:
        raise ValueError("คะแนนต้องเป็น 1–5 และความคิดเห็นไม่เกิน 255 ตัวอักษร")
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT cust_id, status FROM food_order WHERE order_id=%s FOR UPDATE", (order_id,))
        order = cur.fetchone()
        if not order or order["cust_id"] != cust_id or order["status"] != "COMPLETED":
            raise ValueError("รีวิวได้เฉพาะออเดอร์ที่เสร็จสิ้นของลูกค้าที่เลือก")
        if review_id is None:
            cur.execute("INSERT INTO review (cust_id,order_id,rating,comment) VALUES (%s,%s,%s,%s)",
                        (cust_id, order_id, rating, comment))
            new_id = cur.lastrowid
        else:
            cur.execute("SELECT review_id FROM review WHERE review_id=%s FOR UPDATE", (review_id,))
            if not cur.fetchone():
                raise ValueError("ไม่พบรีวิว")
            cur.execute("UPDATE review SET cust_id=%s,order_id=%s,rating=%s,comment=%s WHERE review_id=%s",
                        (cust_id, order_id, rating, comment, review_id))
            new_id = None
        conn.commit()
        return dict(new_id=new_id, affected=1)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def cancel_payment(payment_id, data):
    """ยกเลิกรายการรับเงินที่บันทึกผิดเท่านั้น ไม่ใช่การคืนเงินจริง"""
    if not isinstance(data, dict):
        raise ValueError("ข้อมูลยกเลิกบิลไม่ถูกต้อง")
    reason = data.get("reason")
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 255:
        raise ValueError("กรุณาระบุเหตุผลยกเลิกบิล 1–255 ตัวอักษร")
    if data.get("confirm_no_money_received") is not True:
        raise ValueError("ต้องยืนยันว่าบิลนี้บันทึกผิดและยังไม่ได้รับเงินจริง ไม่ใช้แทนการคืนเงิน")
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT order_id FROM payment WHERE payment_id=%s", (payment_id,))
        reference = cur.fetchone()
        if not reference:
            raise ValueError("ไม่พบบิลที่ต้องการยกเลิก")
        # ล็อกหัวออเดอร์ก่อน payment ให้ตรงกับขั้นตอนรับเงินและแก้ไขออเดอร์
        cur.execute("SELECT order_id FROM food_order WHERE order_id=%s FOR UPDATE", (reference["order_id"],))
        if not cur.fetchone():
            raise ValueError("ไม่พบออเดอร์ของบิล")
        cur.execute("SELECT payment_id, status FROM payment WHERE payment_id=%s FOR UPDATE", (payment_id,))
        payment = cur.fetchone()
        if payment["status"] != "PAID":
            raise ValueError("บิลนี้ถูกยกเลิกแล้ว")
        # คงยอดเดิมและ snapshot ไว้ทั้งหมด เปลี่ยนเฉพาะสถานะและข้อมูลการยกเลิก
        cur.execute("""UPDATE payment SET status='CANCELLED', cancel_reason=%s,
            cancelled_at=CURRENT_TIMESTAMP WHERE payment_id=%s AND status='PAID'""",
            (reason.strip(), payment_id))
        if cur.rowcount != 1:
            raise ValueError("สถานะบิลเปลี่ยนแล้ว กรุณาโหลดรายการใหม่")
        conn.commit()
        return dict(payment_id=payment_id, order_id=reference["order_id"], status="CANCELLED")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def delete_receipt(payment_id):
    """เอาใบเสร็จออกจากรายการเท่านั้น คงรายการรับเงินและสถานะออเดอร์ไว้"""
    conn = db.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT payment_id FROM payment WHERE payment_id=%s FOR UPDATE", (payment_id,))
        if not cur.fetchone():
            raise ValueError("ไม่พบใบเสร็จ")
        # ไม่แก้ status/total/snapshot และไม่ลบ payment เพื่อไม่ให้รับชำระซ้ำ
        cur.execute("UPDATE payment SET receipt_deleted_at=COALESCE(receipt_deleted_at,CURRENT_TIMESTAMP) WHERE payment_id=%s", (payment_id,))
        conn.commit()
        return dict(payment_id=payment_id, deleted=True)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
