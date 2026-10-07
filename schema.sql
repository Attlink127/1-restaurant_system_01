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
    member_tier ENUM('Regular', 'Silver', 'Gold', 'Platinum')
        NOT NULL DEFAULT 'Regular'
);

-- 2. เมนูอาหาร

CREATE TABLE menu_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM('APPETIZER', 'MAIN_COURSE', 'DESSERT', 'DRINK')
        NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,

    CHECK (price >= 0),

    -- เมนูยกเลิกถาวรต้องไม่เปิดขาย
    CHECK (is_discontinued = FALSE OR is_available = FALSE)
);

-- 3. โต๊ะอาหาร
CREATE TABLE dining_table (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    seats INT NOT NULL,
    zone ENUM('INDOOR', 'OUTDOOR') NOT NULL,

    CHECK (seats > 0)
);

-- 4. ออเดอร์

CREATE TABLE food_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    cust_id INT NOT NULL,
    table_id INT NOT NULL,
    order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
        NOT NULL DEFAULT 'PENDING',

    FOREIGN KEY (cust_id)
        REFERENCES customer(cust_id),

    FOREIGN KEY (table_id)
        REFERENCES dining_table(table_id)
);


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
INSERT INTO customer (cust_id, name, phone, member_tier)
VALUES
(1, 'เจ๋ง',   '0800000001', 'Silver'),
(2, 'พีท',   '0800000002', 'Regular'),
(3, 'บีม',   '0800000003', 'Platinum'),	
(4, 'ปอ',   '0800000004', 'Regular'),
(5, 'เบส',   '0800000005', 'Gold');


-- 2. เมนูอาหาร 11 รายการ รวมเมนูชุด 2 ชุด

INSERT INTO menu_item
(item_id, name, category, price, is_available, is_discontinued)
VALUES
(1, 'ซุปเห็ดทรัฟเฟิล',
 'APPETIZER', 129.00, TRUE, FALSE),

(2, 'กุ้งทอดซอสครีม',
 'APPETIZER', 159.00, TRUE, FALSE),

(3, 'แกงหน่อไม้',
 'MAIN_COURSE', 89.00, TRUE, FALSE),

(4, 'สเต๊กเนื้อซอสไวน์แดง',
 'MAIN_COURSE', 359.00, TRUE, FALSE),

(5, 'พาสตากุ้งครีมซอส',
 'MAIN_COURSE', 229.00, TRUE, FALSE),

(6, 'พุดดิ้งวานิลลา',
 'DESSERT', 79.00, TRUE, FALSE),

(7, 'ช็อกโกแลตลาวา',
 'DESSERT', 119.00, TRUE, FALSE),

(8, 'ชาพีช',
 'DRINK', 59.00, TRUE, FALSE),

(9, 'ลิ้นจี่โซดา',
 'DRINK', 69.00, TRUE, FALSE),

(10, 'ชุดสเต๊กสุดคุ้ม',
 'MAIN_COURSE', 449.00, TRUE, FALSE),

(11, 'ชุดพาสต้าสุดคุ้ม',
 'MAIN_COURSE', 279.00, TRUE, FALSE);


-- 3. โต๊ะอาหาร 5 โต๊ะ

INSERT INTO dining_table (table_id, seats, zone)
VALUES
(1, 2, 'INDOOR'),
(2, 4, 'INDOOR'),
(3, 4, 'OUTDOOR'),
(4, 6, 'INDOOR'),
(5, 8, 'OUTDOOR');


-- 4. ออเดอร์ 5 รายการ
-- กำหนดให้ COMPLETED หมายถึงเสร็จและชำระเงินแล้ว

INSERT INTO food_order
(order_id, cust_id, table_id, order_time, status)
VALUES
(1, 1, 4, '2026-09-28 12:00:00', 'COMPLETED'),
(2, 2, 1, '2026-09-28 18:00:00', 'COMPLETED'),
(3, 3, 2, '2026-09-29 12:00:00', 'COMPLETED'),
(4, 4, 5, '2026-09-29 13:00:00', 'COMPLETED'),
(5, 5, 3, '2026-09-29 14:00:00', 'CANCELLED');


-- 5. รายการอาหารในออเดอร์ 10 แถว
-- unit_price คือราคาต่อหน่วย ณ เวลาสั่ง

INSERT INTO order_item
(order_id, item_id, qty, unit_price, note)
VALUES
-- ออเดอร์ 1: สเต๊ก 2 + ชาพีช 2 = 836 บาท
(1, 4, 2, 359.00, 'เนื้อสุกปานกลาง'),
(1, 8, 2, 59.00, 'หวานน้อย'),

-- ออเดอร์ 2: แกงหน่อไม้ 1 + กุ้งทอด 1 = 248 บาท
(2, 3, 1, 89.00, 'เผ็ดน้อย'),
(2, 2, 1, 159.00, 'แยกซอส'),

-- ออเดอร์ 3: ชุดพาสต้า 2 + ช็อกโกแลตลาวา 1 = 677 บาท
(3, 11, 2, 279.00, NULL),
(3, 7, 1, 119.00, NULL),

-- ออเดอร์ 4: ชุดสเต๊ก 3 + ซุปเห็ด 2 = 1,605 บาท
(4, 10, 3, 449.00, NULL),
(4, 1, 2, 129.00, NULL),

-- ออเดอร์ 5: พาสต้า 1 + ลิ้นจี่โซดา 1 = 298 บาท
-- ออเดอร์นี้ยกเลิก จึงไม่นับยอดขาย
(5, 5, 1, 229.00, NULL),
(5, 9, 1, 69.00, 'ไม่ใส่น้ำแข็ง');


-- 6. ส่วนประกอบชุดอาหาร 5 แถว

INSERT INTO combo (item_id, sub_item_id, amount)
VALUES
-- ชุดสเต๊ก: สเต๊ก 1 + พุดดิ้ง 1 + ชาพีช 1
(10, 4, 1),
(10, 6, 1),
(10, 8, 1),
-- ชุดพาสต้า: พาสต้า 1 + ลิ้นจี่โซดา 1
(11, 5, 1),
(11, 9, 1);
ิื

--   ★ ควรมีออเดอร์ status 'open' อย่างน้อย 1 โต๊ะ ไว้ทดสอบ "เปิดออเดอร์ซ้ำโต๊ะเดิมไม่ได้"
