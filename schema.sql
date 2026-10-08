-- ============================================================
--  schema.sql — ระบบร้านอาหาร (นิสิตออกแบบและเขียนเอง)
--  กติกา: 1 ออเดอร์มีหลายเมนู (M:N: order × menu_item ผ่าน order_item),
--         เมนูชุด combo = M:N (menu_item × menu_item)
--  ต้องมี: PK ทุกตาราง, FK ครบ, ชื่อตรงกับ db.py, sample data
-- ============================================================
--

-- 1. ลูกค้า
CREATE TABLE customer (
    cust_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    member_tier ENUM('Regular', 'silver', 'gold')
        NOT NULL DEFAULT 'Regular'
);


-- 2. เมนูอาหาร

CREATE TABLE menu_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM(
        'APPETIZER','MAIN_COURSE','DESSERT','DRINK') NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,

    CHECK (price >= 0),
    CHECK (
        is_discontinued = FALSE
        OR is_available = FALSE
    )
);

-- 3. โต๊ะอาหาร
CREATE TABLE dining_table (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    seats INT NOT NULL,
    zone ENUM('INDOOR', 'OUTDOOR', 'VIP') NOT NULL,

    CHECK (seats > 0)
);

-- 4. ออเดอร์
-- open = ยังไม่ชำระเงิน
-- paid = ชำระเงินแล้ว
CREATE TABLE food_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT NOT NULL,
    table_id INT NOT NULL,
    order_time DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    status ENUM('open', 'paid')
        NOT NULL DEFAULT 'open',

    FOREIGN KEY (cust_id)
        REFERENCES customer(cust_id),

    FOREIGN KEY (table_id)
        REFERENCES dining_table(table_id)
)


-- 5. รายการอาหารในออเดอร์
-- เชื่อม food_order กับ menu_item

CREATE TABLE order_item (
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    note VARCHAR(255),

    PRIMARY KEY (order_id, item_id),

    FOREIGN KEY (order_id)
        REFERENCES food_order(order_id),

    FOREIGN KEY (item_id)
        REFERENCES menu_item(item_id),

    CHECK (qty > 0),
    CHECK (unit_price >= 0)
);


-- 6. ส่วนประกอบของชุดอาหาร
-- item_id     = รหัสเมนูชุด
-- sub_item_id = รหัสเมนูภายในชุด
-- amount      = จำนวนเมนูนั้นต่อหนึ่งชุด

CREATE TABLE combo (
    combo_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    sub_item_id INT NOT NULL,
    amount INT NOT NULL,

    FOREIGN KEY (item_id)
        REFERENCES menu_item(item_id),

    FOREIGN KEY (sub_item_id)
        REFERENCES menu_item(item_id),

    UNIQUE (item_id, sub_item_id),

    CHECK (item_id <> sub_item_id),
    CHECK (amount > 0)
);




-- TODO: INSERT ข้อมูลตัวอย่างทุกตาราง
-- ลูกค้า 6 คน
-- ============================================
-- ส่วนที่ 3 เพิ่มข้อมูลตัวอย่าง
-- ============================================

-- 1. ลูกค้า 6 คน
INSERT INTO customer
(cust_id, name, phone, member_tier)
VALUES
(1, 'เจ๋ง', '0800000001', 'gold'),
(2, 'พีท', '0800000002', 'Regular'),
(3, 'บีม', '0800000003', 'gold'),
(4, 'ปอ', '0800000004', 'silver'),
(5, 'เบส', '0800000005', 'gold'),
(6, 'บอส', '0800000006', 'gold');


-- 2. เมนูอาหาร 11 รายการ
INSERT INTO menu_item
(item_id, name, category, price,
 is_available, is_discontinued)
VALUES
(1, 'ซุปเห็ดทรัฟเฟิล', 'APPETIZER', 129, TRUE, FALSE),
(2, 'กุ้งทอดซอสครีม', 'APPETIZER', 159, TRUE, FALSE),
(3, 'แกงหน่อไม้', 'MAIN_COURSE', 89, TRUE, FALSE),
(4, 'สเต๊กเนื้อซอสไวน์แดง', 'MAIN_COURSE', 359, TRUE, FALSE),
(5, 'พาสตากุ้งครีมซอส', 'MAIN_COURSE', 229, TRUE, FALSE),
(6, 'พุดดิ้งวานิลลา', 'DESSERT', 79, TRUE, FALSE),
(7, 'ช็อกโกแลตลาวา', 'DESSERT', 119, TRUE, FALSE),
(8, 'ชาพีช', 'DRINK', 59, TRUE, FALSE),
(9, 'ลิ้นจี่โซดา', 'DRINK', 69, TRUE, FALSE),
(10, 'ชุดสเต๊กสุดคุ้ม', 'MAIN_COURSE', 449, TRUE, FALSE),
(11, 'ชุดพาสต้าสุดคุ้ม', 'MAIN_COURSE', 279, TRUE, FALSE);


-- 3. โต๊ะอาหาร 7 โต๊ะ
-- โต๊ะ 7 เป็นโซน VIP รองรับ 6 คน
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


-- 4. ออเดอร์ 6 รายการ
-- บีมเป็นสมาชิก gold ใช้โต๊ะ VIP หมายเลข 7
INSERT INTO food_order
(order_id, cust_id, table_id, order_time, status)
VALUES
(1, 1, 4, '2026-09-28 12:00:00', 'paid'),
(2, 2, 1, '2026-09-28 18:00:00', 'paid'),
(3, 3, 7, '2026-09-29 12:00:00', 'paid'),
(4, 4, 5, '2026-09-29 13:00:00', 'paid'),
(5, 5, 3, '2026-09-29 14:00:00', 'open'),
(6, 6, 6, '2026-09-29 14:00:00', 'open');


-- 5. รายการอาหารในออเดอร์
-- unit_price คือราคาตอนสั่งจริง
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
(6, 8, 1, 59, NULL);


-- 6. ส่วนประกอบชุดอาหาร
INSERT INTO combo
(item_id, sub_item_id, amount)
VALUES

-- ชุดสเต๊ก
(10, 4, 1),
(10, 6, 1),
(10, 8, 1),

-- ชุดพาสต้า
(11, 5, 1),
(11, 9, 1);
ิื

--   ★ ควรมีออเดอร์ status 'open' อย่างน้อย 1 โต๊ะ ไว้ทดสอบ "เปิดออเดอร์ซ้ำโต๊ะเดิมไม่ได้"
