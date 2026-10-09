# ============================================================
#  app.py — เว็บแอปพลิเคชัน Flask (REST API & Web Server)
#  ทำหน้าที่เป็น Controller คอยรับ Request จากหน้าเว็บ แล้วเรียกฟังก์ชันใน db.py
#  คำสั่งรัน:  python app.py  แล้วเปิดดูที่ http://127.0.0.1:5000
#  ★ โครงสร้างการทำงาน:  หน้าเว็บ (HTML/JS) → app.py (เส้นทาง API) → db.py (SQL) → MySQL
# ============================================================
from datetime import date, datetime
# Flask = เฟรมเวิร์กเว็บ, request = อ่านค่าที่ส่งมาจากฝั่งเว็บ, jsonify = ตอบกลับเป็น JSON, render_template = เรนเดอร์ไฟล์ HTML
from flask import Flask, request, jsonify, render_template
from flask.json.provider import DefaultJSONProvider
import db  # โมดูลที่เก็บฟังก์ชันติดต่อฐานข้อมูลทั้งหมด (ชั้น Model)


# ------------------------------------------------------------
# 1. ปรับแต่งการแปลงข้อมูลเป็น JSON (Custom JSON Provider)
# ------------------------------------------------------------
class JSONProvider(DefaultJSONProvider):
    """
    - แปลงข้อมูลประเภท วันที่และเวลา (date, datetime) ให้อยู่ในฟอร์แมตมาตรฐาน ISO (YYYY-MM-DDTHH:MM:SS)
      เพื่อให้ช่อง Input ประเภท date/datetime-local ในหน้าเว็บสามารถอ่านและแสดงผลได้ถูกต้อง
    - กำหนด sort_keys = False เพื่อไม่ให้สลับลำดับคอลัมน์ใหม่ ทำให้หัวตารางบนหน้าเว็บเรียงตรงตามที่ SELECT มาใน SQL
    """
    sort_keys = False

    @staticmethod
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


# สร้าง Instance ของ Flask Application
# __name__ บอก Flask ว่ารากของโปรเจกต์อยู่ตรงไหน เพื่อหาโฟลเดอร์ templates/ และ static/ ได้
app = Flask(__name__)
app.json = JSONProvider(app)  # ใช้ JSONProvider ที่เราปรับแต่งเองด้านบน


# ------------------------------------------------------------
# 2. ฟังก์ชันตัวช่วยดักจับ Error (Helper Error Handler)
# ------------------------------------------------------------
def safe(fn, *args, **kwargs):
    """
    ฟังก์ชันครอบ (Wrapper) สำหรับเรียกใช้คำสั่งใน db.py อย่างปลอดภัย
    - ถ้าสำเร็จ: ส่งค่ากลับเป็น JSON {"ok": True, "data": ผลลัพธ์} (HTTP 200)
    - ถ้าเป็น NotImplementedError: ส่งกลับสถานะ 501 (ฟังก์ชันที่ยังไม่ได้ทำ)
    - ถ้าเป็น ValueError: ส่งข้อผิดพลาดทางธุรกิจ (เช่น โต๊ะไม่ว่าง, เมนูซ้ำ) กลับไปเป็น HTTP 400 ให้หน้าเว็บ alert เตือนผู้ใช้
    - ถ้าเป็น Exception อื่นๆ: ส่งกลับสถานะ HTTP 500 (Server Error)
    """
    try:
        # เรียกฟังก์ชันจริงใน db.py พร้อมส่ง argument ที่รับมาจาก HTTP Request
        return jsonify({"ok": True, "data": fn(*args, **kwargs)})
    except NotImplementedError as e:
        # ฟังก์ชันที่ยังเขียนไม่เสร็จ (กรณีโครงงานตั้งต้น) → HTTP 501
        return jsonify({"ok": False, "todo": True, "error": str(e)}), 501
    except ValueError as e:
        # แจ้งเตือนข้อผิดพลาดที่ db.py ดักจับไว้ เช่น raise ValueError("โต๊ะนี้ยังไม่ว่าง")
        # เป็นความผิดของผู้ใช้ (HTTP 400) → หน้าเว็บจะ alert ข้อความนี้
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        # ข้อผิดพลาดอื่นที่คาดไม่ถึง (bug / ฐานข้อมูลล่ม) → HTTP 500
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500


# ------------------------------------------------------------
# 3. เส้นทางหน้าเว็บ (HTML Page Routes)
# ------------------------------------------------------------
@app.route("/")
def page_home():
    """หน้าหลัก: หน้าจัดการข้อมูลระบบร้านอาหาร (ลูกค้า, เมนู, คอมโบ, ออเดอร์, รีวิว)"""
    return render_template("index.html")

@app.route("/report")
def page_report():
    """หน้ารายงาน: แสดงการ์ดสรุปตัวเลขสถิติ และตารางรายงานผลการดำเนินงาน"""
    return render_template("report.html")


# ------------------------------------------------------------
# 4. REST API: ข้อมูลลูกค้า (Customer API)
# ------------------------------------------------------------
@app.route("/api/customers", methods=["GET"])
def customers_list():
    """ดึงรายชื่อลูกค้าตามเงื่อนไขค้นหา (ชื่อ, เบอร์โทร, ระดับสมาชิก)"""
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_customers, filters)

@app.route("/api/customers/<int:_id>", methods=["GET"])
def customer_get(_id):
    """ดึงข้อมูลลูกค้ารายบุคคลตาม cust_id (ใช้สำหรับเปิดฟอร์มแก้ไข)"""
    return safe(db.get_customer, _id)

@app.route("/api/customers", methods=["POST"])
def customer_create():
    """เพิ่มข้อมูลลูกค้าใหม่ลงฐานข้อมูล"""
    # request.json = อ่าน body ที่ฝั่งเว็บส่งมาเป็น JSON (Content-Type: application/json)
    return safe(db.create_customer, request.json)

@app.route("/api/customers/<int:_id>", methods=["PUT"])
def customer_update(_id):
    """แก้ไขข้อมูลลูกค้าตาม cust_id"""
    return safe(db.update_customer, _id, request.json)

@app.route("/api/customers/<int:_id>", methods=["DELETE"])
def customer_delete(_id):
    """ลบข้อมูลลูกค้าออกจากระบบ (ถ้ามีประวัติออเดอร์จะลบไม่ได้)"""
    return safe(db.delete_customer, _id)


# ------------------------------------------------------------
# 5. REST API: เมนูอาหาร (Menu Item API)
# ------------------------------------------------------------
@app.route("/api/menu-items", methods=["GET"])
def items_list():
    """ดึงรายการเมนูอาหารตามเงื่อนไข (ชื่อเมนู, หมวดหมู่)"""
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_items, filters)

@app.route("/api/menu-items/<int:_id>", methods=["GET"])
def item_get(_id):
    """ดึงข้อมูลเมนู 1 รายการตาม item_id"""
    return safe(db.get_item, _id)

@app.route("/api/menu-items", methods=["POST"])
def item_create():
    """เพิ่มเมนูอาหารใหม่ (ชื่อ, หมวดหมู่, ราคา, สถานะพร้อมขาย)"""
    return safe(db.create_item, request.json)

@app.route("/api/menu-items/<int:_id>", methods=["PUT"])
def item_update(_id):
    """แก้ไขข้อมูลเมนูอาหารตาม item_id"""
    return safe(db.update_item, _id, request.json)

@app.route("/api/menu-items/<int:_id>", methods=["DELETE"])
def item_delete(_id):
    """ลบเมนูอาหาร (ถ้าเคยถูกสั่งหรืออยู่ในคอมโบ ระบบจะแจ้งเตือนให้ปิดการขายแทน)"""
    return safe(db.delete_item, _id)


# ------------------------------------------------------------
# 6. REST API: ชุดคอมโบ (Combo Set API)
# ------------------------------------------------------------
@app.route("/api/combos", methods=["GET"])
def combos_list():
    """ดึงรายการส่วนประกอบของชุดคอมโบทั้งหมด พร้อมราคาเซ็ต"""
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_combos, filters)

@app.route("/api/combos", methods=["POST"])
def combo_create():
    """เพิ่มเมนูย่อยลงในชุดคอมโบ พร้อมระบุจำนวนและราคาเซ็ต"""
    return safe(db.create_combo, request.json)

@app.route("/api/combos/<int:item_id>/<int:sub_item_id>", methods=["GET"])
def combo_get(item_id, sub_item_id):
    """ดึงข้อมูลส่วนประกอบของคอมโบรายการที่ระบุ"""
    return safe(db.get_combo, item_id, sub_item_id)

@app.route("/api/combos/<int:item_id>/<int:sub_item_id>", methods=["PUT"])
def combo_update(item_id, sub_item_id):
    """แก้ไขจำนวนและราคาของเมนูในชุดคอมโบ"""
    return safe(db.update_combo, item_id, sub_item_id, request.json)

@app.route("/api/combos/<int:item_id>/<int:sub_item_id>", methods=["DELETE"])
def combo_delete(item_id, sub_item_id):
    """ลบเมนูย่อยออกจากชุดคอมโบ"""
    return safe(db.delete_combo, item_id, sub_item_id)


# ------------------------------------------------------------
# 7. REST API: ออเดอร์อาหาร (Food Order API)
# ------------------------------------------------------------
@app.route("/api/orders", methods=["GET"])
def orders_list():
    """ดึงรายการออเดอร์ทั้งหมด พร้อมยอดรวมเงินที่คำนวณอัตโนมัติจากรายการอาหาร"""
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_orders, filters)

@app.route("/api/orders/<int:_id>", methods=["GET"])
def order_get(_id):
    """ดึงข้อมูลออเดอร์ 1 รายการตาม order_id"""
    return safe(db.get_order, _id)

@app.route("/api/orders", methods=["POST"])
def order_create():
    """เปิดออเดอร์ใหม่ (มีการตรวจสอบ check_table_free ว่าโต๊ะว่างหรือไม่ก่อนบันทึก)"""
    return safe(db.create_order, request.json)

@app.route("/api/orders/<int:_id>", methods=["PUT"])
def order_update(_id):
    """แก้ไขสถานะออเดอร์หรือเปลี่ยนโต๊ะ"""
    return safe(db.update_order, _id, request.json)

@app.route("/api/orders/<int:_id>", methods=["DELETE"])
def order_delete(_id):
    """ลบออเดอร์ออกจากระบบ (ลบรายการ order_item ภายในออเดอร์ก่อนอัตโนมัติ)"""
    return safe(db.delete_order, _id)


# ------------------------------------------------------------
# 8. REST API: รีวิวร้านอาหาร (Review API)
# ------------------------------------------------------------
@app.route("/api/reviews", methods=["GET"])
def reviews_list():
    """ดึงรายการรีวิวและความคิดเห็นของลูกค้าตามคะแนนดาวหรือข้อความ"""
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_reviews, filters)

@app.route("/api/reviews/<int:_id>", methods=["GET"])
def review_get(_id):
    """ดึงข้อมูลรีวิว 1 รายการตาม review_id"""
    return safe(db.get_review, _id)

@app.route("/api/reviews", methods=["POST"])
def review_create():
    """เพิ่มรีวิวและให้คะแนนดาวร้านอาหาร (1-5 ดาว)"""
    return safe(db.create_review, request.json)

@app.route("/api/reviews/<int:_id>", methods=["PUT"])
def review_update(_id):
    """แก้ไขคะแนนหรือข้อความรีวิว"""
    return safe(db.update_review, _id, request.json)

@app.route("/api/reviews/<int:_id>", methods=["DELETE"])
def review_delete(_id):
    """ลบรีวิวออกจากระบบ"""
    return safe(db.delete_review, _id)


# ------------------------------------------------------------
# 9. REST API: รายงานสถิติและการวิเคราะห์ (Reports API)
# ------------------------------------------------------------
@app.route("/api/reports/summary")
def report_summary():
    """ดึงข้อมูลตัวเลขสรุปสำหรับแสดงผลบน Dashboard การ์ดสรุป"""
    return safe(db.report_summary)

@app.route("/api/reports")
def report_list():
    """ส่งรายชื่อรายงานทั้งหมดที่มีในระบบ (อ่านจากตัวแปร db.REPORTS) ให้หน้าเว็บสร้างกล่องรายงานอัตโนมัติ"""
    return jsonify({"ok": True, "data": [{"key": k, "title": t} for k, t, _ in db.REPORTS]})

@app.route("/api/reports/<key>")
def report_run(key):
    """สั่งรันฟังก์ชันรายงานตามชื่อ key เช่น /api/reports/popular-items"""
    # วนหาคู่ (key, title, function) ใน REPORTS ให้ตรงกับ key ใน URL
    for k, _, fn in db.REPORTS:
        if k == key:
            return safe(fn)  # เรียกฟังก์ชันรายงานตัวนั้น
    # ถ้าไม่พบ key ในรายการ REPORTS → HTTP 404
    return jsonify({"ok": False, "error": f"ไม่พบรายงาน '{key}' ใน db.REPORTS"}), 404


# ------------------------------------------------------------
# 10. จุดเริ่มต้นการรันเซิร์ฟเวอร์ (Server Entry Point)
# ------------------------------------------------------------
if __name__ == "__main__":
    # รันเว็บเซิร์ฟเวอร์ในโหมด Debug พอร์ต 5000 (http://127.0.0.1:5000)
    # debug=True → แก้โค้ดแล้วเซิร์ฟเวอร์รีสตาร์ทเอง และแสดงหน้า Error ละเอียด (ควรปิดตอน deploy จริง)
    app.run(debug=True, port=5000)
