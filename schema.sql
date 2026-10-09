


# ============================================================
#  schema.sql — สร้างโครงสร้างฐานข้อมูล (DDL) + ใส่ข้อมูลตัวอย่าง (DML)
#  ลำดับการทำงานในไฟล์: USE → CREATE TABLE (ตารางแม่ → ตารางลูก) → INSERT ข้อมูลตัวอย่าง
#  หมายเหตุ: ตารางลูกที่มี FOREIGN KEY ต้องสร้าง "หลัง" ตารางแม่ที่มันอ้างถึงเสมอ
# ============================================================
USE project69;   # เลือกใช้ฐานข้อมูลชื่อ project69 ก่อนสร้างตาราง

# ------------------------------------------------------------
# 1. ตารางลูกค้า (customer)
#    เก็บข้อมูลลูกค้าและระดับสมาชิก
# ------------------------------------------------------------
CREATE TABLE customer (
    cust_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    member_tier ENUM('Regular', 'Gold', 'VIP')
        NOT NULL DEFAULT 'Regular'
);


# ------------------------------------------------------------
# 2. ตารางเมนูอาหาร (menu_item)
#    เก็บเมนูทั้งหมด รวมทั้งเมนูที่เป็น "ชุดคอมโบ" (category = 'ชุดคอมโบ')
# ------------------------------------------------------------
CREATE TABLE menu_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM(
        'อาหารเรียกน้ำย่อย',
        'อาหารจานหลัก',
        'ของหวาน',
        'เครื่องดื่ม',
        'ชุดคอมโบ'
    ) NOT NULL,
    price DECIMAL(10,2) NOT NULL,                          # ราคา ทศนิยม 2 ตำแหน่ง
    is_available BOOLEAN NOT NULL DEFAULT TRUE,            # พร้อมขายหรือไม่ (TRUE = พร้อมขาย)
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,        # เลิกขายถาวรหรือไม่

    # ---- เงื่อนไขบังคับ (CHECK CONSTRAINT) ----
    CHECK (price >= 0),                                    # ราคาติดลบไม่ได้
    CHECK (
        is_discontinued = FALSE
        OR is_available = FALSE
    )                                                      # ถ้า "เลิกขาย" ต้องไม่ "พร้อมขาย" (ห้ามเป็น TRUE ทั้งคู่)
);




# ------------------------------------------------------------
# 3. ตารางโต๊ะอาหาร (dining_table)
#    เก็บโต๊ะแต่ละตัว จำนวนที่นั่ง และโซนที่ตั้ง
# ------------------------------------------------------------
CREATE TABLE dining_table (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    seats INT NOT NULL,
    zone ENUM('INDOOR', 'OUTDOOR', 'VIP') NOT NULL,        # โซนโต๊ะ (ในร้าน/นอกร้าน/วีไอพี)

    CHECK (seats > 0)                                      # จำนวนที่นั่งต้องมากกว่า 0
);



# ------------------------------------------------------------
# 4. ตารางออเดอร์ (food_order)
#    ใบสั่งอาหาร 1 ใบ = 1 แถว อ้างอิงลูกค้าและโต๊ะ
# ------------------------------------------------------------
CREATE TABLE food_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT NOT NULL,
    table_id INT NOT NULL,
    order_time DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    status ENUM(
        'PENDING',
        'IN_PROGRESS',
        'COMPLETED',
        'CANCELLED'
    ) NOT NULL DEFAULT 'PENDING',                           # สถานะออเดอร์ เริ่มต้น = รอดำเนินการ

    # ---- คีย์นอก: ผูกกับตาราง customer และ dining_table ----
    # ทำให้ออเดอร์ต้องอ้างลูกค้า/โต๊ะที่มีอยู่จริง (อ้างค่าไม่มี → ใส่ไม่ได้)
    FOREIGN KEY (cust_id)
        REFERENCES customer(cust_id),

    FOREIGN KEY (table_id)
        REFERENCES dining_table(table_id)
);




# ------------------------------------------------------------
# 5. ตารางรายการอาหารในออเดอร์ (order_item)
#    เชื่อมออเดอร์กับเมนู (ความสัมพันธ์แบบ many-to-many)
# ------------------------------------------------------------
CREATE TABLE order_item (
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    note VARCHAR(255),                                     # หมายเหตุพิเศษ (ใส่หรือไม่ใส่ก็ได้ → NULL ได้)

    # ---- คีย์หลักแบบรวม (composite key) ----
    # 1 ออเดอร์มีเมนูเดิมซ้ำเป็น 2 แถวไม่ได้ (คู่ order_id+item_id ต้องไม่ซ้ำ)
    PRIMARY KEY (order_id, item_id),

    FOREIGN KEY (order_id)
        REFERENCES food_order(order_id),

    FOREIGN KEY (item_id)
        REFERENCES menu_item(item_id),

    CHECK (qty > 0),                                       # จำนวนสั่งต้องมากกว่า 0
    CHECK (unit_price >= 0)                                # ราคาต่อหน่วยติดลบไม่ได้
);




# ------------------------------------------------------------
# 6. ตารางชุดคอมโบ (combo)
#    บอกว่า "เมนูชุดหลัก" ประกอบด้วย "เมนูย่อย" อะไร จำนวนเท่าไร
#    (self-referencing: ทั้ง item_id และ sub_item_id ต่างอ้างตาราง menu_item)
# ------------------------------------------------------------
CREATE TABLE combo (
    combo_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    sub_item_id INT NOT NULL,
    amount INT NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,             # ราคาของชุดคอมโบ

    # ทั้ง 2 คอลัมน์อ้างถึงตาราง menu_item เหมือนกัน (เมนูชุดหลัก vs เมนูย่อย)
    FOREIGN KEY (item_id)
        REFERENCES menu_item(item_id),

    FOREIGN KEY (sub_item_id)
        REFERENCES menu_item(item_id),

    UNIQUE (item_id, sub_item_id),                         # เมนูย่อยตัวเดียวกันใส่ซ้ำในชุดเดิมไม่ได้

    CHECK (item_id <> sub_item_id),                        # เมนูชุดหลักกับเมนูย่อยต้องไม่ใช่เมนูเดียวกัน
    CHECK (amount > 0),                                    # จำนวนในชุดต้องมากกว่า 0
    CHECK (price >= 0)                                     # ราคาติดลบไม่ได้
);




# ------------------------------------------------------------
# 7. ตารางรีวิวร้านอาหาร (review)
#    ลูกค้าให้คะแนนดาว + เขียนความคิดเห็น (อาจอ้างอิงถึงออเดอร์ที่มารับประทาน)
# ------------------------------------------------------------
CREATE TABLE review (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT NOT NULL,
    order_id INT,
    rating INT NOT NULL,
    comment VARCHAR(255),                                  # ข้อความรีวิว (เว้นว่างได้)
    review_time DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,                         # ถ้าไม่ระบุเวลา ให้ใช้เวลาปัจจุบัน

    FOREIGN KEY (cust_id)
        REFERENCES customer(cust_id),

    FOREIGN KEY (order_id)
        REFERENCES food_order(order_id),                   # order_id ไม่ใส่ NOT NULL → รีวิวโดยไม่อ้างออเดอร์ก็ได้

    CHECK (rating BETWEEN 1 AND 5)                         # คะแนนต้องอยู่ระหว่าง 1–5 ดาว
);



# ============================================================
#  ส่วนที่ 2: ข้อมูลตัวอย่าง (Seed Data)
#  ★ ลำดับการ INSERT: ตารางแม่ก่อนตารางลูก (เพราะมี FOREIGN KEY)
#    customer/dining_table → menu_item → food_order → order_item/combo → review
# ============================================================

# ---------- ข้อมูลลูกค้า 6 คน ----------
INSERT INTO customer
(cust_id, name, phone, member_tier)
VALUES
(1, 'เจ๋ง', '0800000001', 'Gold'),
(2, 'พีท', '0800000002', 'Regular'),
(3, 'บีม', '0800000003', 'VIP'),
(4, 'ปอ', '0800000004', 'Regular'),
(5, 'เบส', '0800000005', 'Gold'),
(6, 'บอส', '0800000006', 'Gold');




# ---------- ข้อมูลเมนูอาหาร 11 รายการ (เป็นเมนู "ชุดคอมโบ" 2 รายการ: id 10, 11) ----------
INSERT INTO menu_item
(item_id, name, category, price,
 is_available, is_discontinued)
VALUES
(1, 'ซุปเห็ดทรัฟเฟิล', 'อาหารเรียกน้ำย่อย', 129, TRUE, FALSE),
(2, 'กุ้งทอดซอสครีม', 'อาหารเรียกน้ำย่อย', 159, TRUE, FALSE),
(3, 'แกงหน่อไม้', 'อาหารจานหลัก', 89, TRUE, FALSE),
(4, 'สเต๊กเนื้อซอสไวน์แดง', 'อาหารจานหลัก', 359, TRUE, FALSE),
(5, 'พาสตากุ้งครีมซอส', 'อาหารจานหลัก', 229, TRUE, FALSE),
(6, 'พุดดิ้งวานิลลา', 'ของหวาน', 79, TRUE, FALSE),
(7, 'ช็อกโกแลตลาวา', 'ของหวาน', 119, TRUE, FALSE),
(8, 'ชาพีช', 'เครื่องดื่ม', 59, TRUE, FALSE),
(9, 'ลิ้นจี่โซดา', 'เครื่องดื่ม', 69, TRUE, FALSE),
(10, 'ชุดสเต๊กสุดคุ้ม', 'ชุดคอมโบ', 449, TRUE, FALSE),
(11, 'ชุดพาสต้าสุดคุ้ม', 'ชุดคอมโบ', 279, TRUE, FALSE);




# ---------- ข้อมูลโต๊ะอาหาร 7 โต๊ะ แยกเป็น 3 โซน ----------
INSERT INTO dining_table
(table_id, seats, zone)
VALUES
(1, 2, 'INDOOR'),
(2, 4, 'INDOOR'),
(3, 4, 'OUTDOOR'),
(4, 6, 'INDOOR'),
(5, 8, 'OUTDOOR'),
(6, 5, 'OUTDOOR'),
(7, 6, 'VIP');




# ---------- ข้อมูลออเดอร์ 7 ใบ (มีทุกสถานะ: COMPLETED/PENDING/IN_PROGRESS/CANCELLED) ----------
INSERT INTO food_order
(order_id, cust_id, table_id, order_time, status)
VALUES
(1, 1, 4, '2026-09-28 12:00:00', 'COMPLETED'),
(2, 2, 1, '2026-09-28 18:00:00', 'COMPLETED'),
(3, 3, 7, '2026-09-29 12:00:00', 'COMPLETED'),
(4, 4, 5, '2026-09-29 13:00:00', 'COMPLETED'),
(5, 5, 3, '2026-09-29 14:00:00', 'PENDING'),
(6, 6, 6, '2026-09-29 14:00:00', 'IN_PROGRESS'),
(7, 2, 2, '2026-09-29 16:00:00', 'CANCELLED');




# ---------- รายการอาหารในแต่ละออเดอร์ (unit_price = ราคาตอนสั่ง ยึดราคานี้เพื่อไม่ให้กระทบย้อนหลัง) ----------
# หมายเหตุ: คอมเมนต์ท้ายแต่ละกลุ่มคือยอดรวมของออเดอร์นั้น (qty × unit_price)
INSERT INTO order_item
(order_id, item_id, qty, unit_price, note)
VALUES

-- ออเดอร์ 1 = 836 บาท
(1, 4, 2, 359, 'เนื้อสุกปานกลาง'),
(1, 8, 2, 59, 'หวานน้อย'),

-- ออเดอร์ 2 = 248 บาท
(2, 3, 1, 89, 'เผ็ดน้อย'),
(2, 2, 1, 159, 'แยกซอส'),

-- ออเดอร์ 3 = 677 บาท
(3, 11, 2, 279, NULL),
(3, 7, 1, 119, NULL),

-- ออเดอร์ 4 = 1605 บาท
(4, 10, 3, 449, NULL),
(4, 1, 2, 129, NULL),

-- ออเดอร์ 5 = 298 บาท
(5, 5, 1, 229, NULL),
(5, 9, 1, 69, 'ไม่ใส่น้ำแข็ง'),

-- ออเดอร์ 6 = 148 บาท
(6, 3, 1, 89, NULL),
(6, 8, 1, 59, NULL),

-- ออเดอร์ 7 (ยกเลิก) = 229 บาท
(7, 5, 1, 229, 'ลูกค้ายกเลิก - ติดธุระด่วน');



# ---------- องค์ประกอบของชุดคอมโบ ----------
# ชุดสเต๊ก (item_id=10) ประกอบด้วย สเต๊ก + พุดดิ้ง + ชาพีช
# ชุดพาสต้า (item_id=11) ประกอบด้วย พาสต้า + ลิ้นจี่โซดา
INSERT INTO combo
(item_id, sub_item_id, amount, price)
VALUES

-- ชุดสเต๊ก (ราคาชุด 449 บาท)
(10, 4, 1, 449.00),
(10, 6, 1, 449.00),
(10, 8, 1, 449.00),

-- ชุดพาสต้า (ราคาชุด 279 บาท)
(11, 5, 1, 279.00),
(11, 9, 1, 279.00);




# ---------- รีวิวร้าน 6 รายการ (คะแนน 4–5 ดาว) อ้างอิงออเดอร์ 1–6 ----------
INSERT INTO review
(review_id, cust_id, order_id, rating, comment, review_time)
VALUES
(1, 1, 1, 5, 'สเต๊กเนื้อซอสไวน์แดงอร่อยมาก ชาพีชหวานกำลังดี ประทับใจมากครับ', '2026-09-28 13:30:00'),
(2, 2, 2, 4, 'แกงหน่อไม้และกุ้งทอดรสชาติดี พนักงานบริการสุภาพ', '2026-09-28 19:15:00'),
(3, 3, 3, 5, 'ชุดพาสต้าสุดคุ้มและช็อกโกแลตลาวาอร่อยมาก บรรยากาศโซน VIP เยี่ยม', '2026-09-29 13:00:00'),
(4, 4, 4, 5, 'ชุดสเต๊กสุดคุ้มคุ้มค่ามาก ซุปเห็ดทรัฟเฟิลหอมกลมกล่อม', '2026-09-29 14:30:00'),
(5, 5, 5, 4, 'อาหารอร่อย รอไม่นาน ลิ้นจี่โซดาสดชื่นดี', '2026-09-29 15:00:00'),
(6, 6, 6, 5, 'บริการรวดเร็ว แกงหน่อไม้รสชาติจัดจ้านกำลังดี แนะนำครับ', '2026-09-29 15:30:00');

