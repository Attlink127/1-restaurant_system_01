// ============================================================
//  app.js  —  ตรรกะหน้าเว็บ (ทำให้เสร็จแล้ว ★ นิสิตไม่ต้องแก้)
//  ปรับช่องค้นหา/ฟอร์มได้ที่ตัวแปร ENTITIES ด้านล่าง
//  ★ หลักการ: ENTITIES เป็น "การตั้งค่า" บอกว่ามี entity อะไร มีช่องค้นหา/ฟอร์มอะไร
//    แล้วโค้ดด้านล่างจะสร้างหน้าจอ ตาราง และยิง API ให้โดยอัตโนมัติ
// ============================================================
// ★ ตัวอย่าง dropdown ที่อ่านข้อมูลจากฐานข้อมูล: ฟอร์ม "ออเดอร์" ช่อง cust_id
//   แสดง name แต่ส่งค่าเป็น cust_id (อ่านรายการจาก /api/customers)
//   ช่อง FK อื่น ๆ ทำแบบเดียวกันได้ — เปลี่ยน "type": "number" เป็น select + optionsFrom

// รายการหมวดหมู่เมนู ใช้เป็นตัวเลือก (options) ของช่อง category
const DINING_ZONES = [
  {value:"INDOOR",label:"ในร้าน"}, {value:"OUTDOOR",label:"นอกร้าน"}, {value:"VIP",label:"VIP"}
];
const ITEM_CATEGORIES = [
  { value: "อาหารเรียกน้ำย่อย", label: "อาหารเรียกน้ำย่อย" },
  { value: "อาหารจานหลัก", label: "อาหารจานหลัก" },
  { value: "ของหวาน", label: "ของหวาน" },
  { value: "เครื่องดื่ม", label: "เครื่องดื่ม" },
  { value: "ชุดคอมโบ", label: "ชุดคอมโบ" }
];
// สถานะของออเดอร์ (ค่าตรงกับ ENUM ในฐานข้อมูล) — value คือค่าที่ส่งไป API, label คือข้อความที่ผู้ใช้เห็น
// แยกค่าที่บันทึกออกจากข้อความที่แสดง: value ต้องเป็นรหัสอังกฤษ เช่น PENDING
// ส่วน label เป็นภาษาไทย เพื่อให้ผู้ใช้เข้าใจ และไม่ส่งภาษาไทยไปชน ENUM ใน MySQL
const ORDER_STATUSES = [
  { value: "PENDING", label: "รอดำเนินการ" },
  { value: "IN_PROGRESS", label: "กำลังดำเนินการ" },
  { value: "READY", label: "พร้อมเสิร์ฟ" },
  { value: "COMPLETED", label: "เสร็จสิ้น" },
  { value: "CANCELLED", label: "ยกเลิก" }
];

// ENTITIES = ศูนย์กลางการตั้งค่าของทั้งหน้าเว็บ: แต่ละ entity บอก label, api, คีย์หลัก, ช่องค้นหา (search) และช่องฟอร์ม (form)
const ENTITIES = {
  // ประวัติรับเงินอ่านอย่างเดียว เพิ่มบิลจากรายละเอียดออเดอร์ เพื่อป้องกันการสร้างบิลลอย
  "payments": {
    label: "การชำระเงิน / ใบเสร็จ", api: "/api/payments", idKey: "payment_id", readOnly: true,
    search: [
      {key: "order_id", label: "เลขออเดอร์", type: "number"},
      {key: "customer_name", label: "ชื่อลูกค้าในใบเสร็จ", type: "text"},
      {key: "payment_date", label: "วันที่ชำระ", type: "date"},
      {key: "method", label: "วิธีชำระ", type: "select", options: [
        {value: "", label: "ทั้งหมด"}, {value: "CASH", label: "เงินสด"}, {value: "TRANSFER", label: "โอนเงิน"}
      ]}
    ], form: []
  },
  // ---------- ลูกค้า (customers) ----------
  "customers": {
    "label": "ลูกค้า",
    "api": "/api/customers",
    "idKey": "cust_id",
    "search": [
      {
        "key": "name",
        "label": "ชื่อ",
        "type": "text"
      },
      {
        "key": "phone",
        "label": "เบอร์โทร",
        "type": "text"
      },
      {
        "key": "member_tier",
        "label": "ระดับ",
        "type": "select",
        "options": [
          "",
          "Regular",
          "Gold",
          "VIP"
        ]
      }
    ],
    "form": [
      {
        "key": "name",
        "label": "ชื่อ",
        "type": "text"
      },
      {
        "key": "phone",
        "label": "เบอร์โทร",
        "type": "text"
      },
      {
        "key": "member_tier",
        "label": "ระดับสมาชิก",
        "type": "select",
        "options": ["Regular", "Gold", "VIP"]
      },
      {
        "type": "heading",
        "label": "เลือกระดับสมาชิกได้เอง ระบบยังเลื่อนตามยอดออเดอร์เสร็จสิ้น: Gold ครบ 3,000 บาท / VIP ครบ 10,000 บาท เมื่อบันทึกออเดอร์ครั้งถัดไป"
      }
    ]
  },
  // ---------- เมนูอาหาร (items) ----------
  "items": {
    "label": "เมนูอาหาร",
    "api": "/api/menu-items",
    "idKey": "item_id",
    "search": [
      {
        "key": "name",
        "label": "ชื่อเมนู",
        "type": "text"
      },
      {
        "key": "category",
        "label": "หมวดหมู่",
        "type": "select",
        "options": [{ value: "", label: "ทั้งหมด" }, ...ITEM_CATEGORIES]
      }
    ],
    "form": [
      {
        "key": "name",
        "label": "ชื่อเมนู",
        "type": "text"
      },
      {
        "key": "category",
        "label": "หมวดหมู่",
        "type": "select",
        "options": ITEM_CATEGORIES
      },
      {
        "key": "price",
        "label": "ราคา",
        "type": "number"
      },
      {
        "key": "is_available",
        "label": "พร้อมขาย",
        "type": "select",
        "options": [
          { value: "1", label: "พร้อมขาย" },
          { value: "0", label: "หมดชั่วคราว" }
        ]
      },
      {
        "key": "is_discontinued",
        "label": "เลิกขาย (เมื่อเลือกเลิกขาย ระบบจะปิดพร้อมขายให้)",
        "type": "select",
        "options": [
          { value: "0", label: "ยังจำหน่าย" },
          { value: "1", label: "เลิกขาย" }
        ]
      }
    ]
  },
  // ---------- ชุดคอมโบ (combos) ----------
  // การสร้างชุดเริ่มจากเพิ่มเมนูชุดหลักใน menu_item หมวดหมู่ "ชุดคอมโบ" พร้อมราคาขายทั้งชุด
  // จากนั้นตาราง combo จะเก็บว่าเมนูชุดหลัก (item_id) ประกอบด้วยเมนูย่อย (sub_item_id) อะไรบ้าง
  // เช่น ชุดสเต๊ก 1 ชุดมี 3 แถว: สเต๊ก 1 จาน, พุดดิ้ง 1 ถ้วย และชา 1 แก้ว
  // amount คือจำนวนเมนูย่อยในชุด ไม่ใช่จำนวนชุดที่ลูกค้าสั่ง
  // ตอนสั่งจริง เลือกเมนูชุดหลักในฟอร์มออเดอร์ ระบบคิดราคาจาก menu_item.price ของชุดนั้น
  // ระบบนี้ยังไม่ได้แตกชุดเป็นรายการเมนูย่อยใน order_item หรือตัดสต็อกวัตถุดิบอัตโนมัติ
  "combos": {
    "label": "ชุดคอมโบ",
    "api": "/api/combos",
    // API อ้างแถวด้วยคู่ UNIQUE นี้; ส่วน PK จริงใน schema คือ combo_id
    "idKeys": ["item_id", "sub_item_id"],
    "search": [
      {
        "key": "combo_name",
        "label": "ชื่อชุด",
        "type": "text"
      },
      {
        "key": "sub_item_name",
        "label": "ชื่อเมนูในชุด",
        "type": "text"
      }
    ],
    "form": [
      {
        "key": "combo_name",
        "label": "ชื่อเซ็ต",
        "type": "text"
      },
      {
        "key": "sub_item_id",
        "label": "เมนูที่ 1",
        "placeholder": "เลือกเมนูที่ 1",
        "type": "select",
        "lockOnEdit": true,
        "optionsFrom": {
          "api": "/api/menu-items",
          "excludeCategory": "ชุดคอมโบ",
          "value": "item_id",
          "label": "name"
        }
      },
      {
        "key": "amount",
        "label": "จำนวนเมนูที่ 1",
        "defaultValue": 1,
        "type": "number"
      },
      {
        "key": "sub_item_id_2", "label": "เมนูที่ 2", "type": "select",
        "createOnly": true, "placeholder": "เลือกเมนูที่ 2",
        "optionsFrom": {"api":"/api/menu-items", "value":"item_id", "label":"name", "excludeCategory":"ชุดคอมโบ"}
      },
      {"key":"amount_2", "label":"จำนวนเมนูที่ 2", "type":"number", "createOnly":true, "defaultValue":1},
      {
        "key": "sub_item_id_3", "label": "เมนูที่ 3", "type": "select",
        "createOnly": true, "placeholder": "เลือกเมนูที่ 3",
        "optionsFrom": {"api":"/api/menu-items", "value":"item_id", "label":"name", "excludeCategory":"ชุดคอมโบ"}
      },
      {"key":"amount_3", "label":"จำนวนเมนูที่ 3", "type":"number", "createOnly":true, "defaultValue":1},
      {
        "key": "price",
        "label": "ราคาขายรวมทั้งเซ็ต",
        "type": "number"
      }
    ]
  },
  // ---------- ออเดอร์ (orders) ----------
  "orders": {
    "label": "ออเดอร์",
    "api": "/api/orders",
    "idKey": "order_id",
    "search": [
      {key:"zone",label:"โซนที่นั่ง",type:"select",options:[{value:"",label:"ทั้งหมด"}, ...DINING_ZONES]},
      {
        "key": "cust_id",
        "label": "รหัสลูกค้า",
        "type": "number"
      },
      {
        "key": "table_id",
        "label": "รหัสโต๊ะ",
        "type": "number"
      },
      {
        "key": "status",
        "label": "สถานะ",
        "type": "select",
        "options": [{ value: "", label: "ทั้งหมด" }, ...ORDER_STATUSES]
      }
    ],
    "form": [
      {
        "key": "cust_id",
        "label": "ลูกค้า",
        "type": "select",
        "optionsFrom": {
          "api": "/api/customers",
          "value": "cust_id",
          "label": "name"
        }
      },
      {key:"zone",label:"โซนที่นั่ง",type:"select",options:[{value:"",label:"เลือกโซนที่นั่ง"}, ...DINING_ZONES]},
      {key:"table_id",label:"โต๊ะ / จำนวนที่นั่ง",type:"select",options:[{value:"",label:"เลือกโซนก่อน"}]},
      {
        "key": "order_time",
        "label": "เวลาสั่ง",
        "type": "datetime-local"
      },
      {
        "key": "status",
        "label": "สถานะ",
        "type": "select",
        "options": ORDER_STATUSES
      }
    ]
  },
  // ---------- รีวิวร้าน (reviews) ----------
  "reviews": {
    "label": "รีวิวร้าน",
    "api": "/api/reviews",
    "idKey": "review_id",
    "search": [
      {
        "key": "rating",
        "label": "คะแนน (ดาว)",
        "type": "select",
        "options": [
          { value: "", label: "ทั้งหมด" },
          { value: "5", label: "⭐⭐⭐⭐⭐ (5 ดาว)" },
          { value: "4", label: "⭐⭐⭐⭐ (4 ดาว)" },
          { value: "3", label: "⭐⭐⭐ (3 ดาว)" },
          { value: "2", label: "⭐⭐ (2 ดาว)" },
          { value: "1", label: "⭐ (1 ดาว)" }
        ]
      },
      {
        "key": "comment",
        "label": "ความคิดเห็น",
        "type": "text"
      }
    ],
    "form": [
      {
        "key": "cust_id",
        "label": "ลูกค้า",
        "type": "select",
        "optionsFrom": {
          "api": "/api/customers",
          "value": "cust_id",
          "label": "name"
        }
      },
      {
        "key": "order_id",
        "label": "ออเดอร์ที่เสร็จสิ้นของลูกค้า",
        "type": "select",
        "options": [{value: "", label: "เลือกออเดอร์"}]
      },
      {
        "key": "rating",
        "label": "คะแนน (1-5 ดาว)",
        "type": "select",
        "options": [
          { value: "5", label: "⭐⭐⭐⭐⭐ (5 ดาว)" },
          { value: "4", label: "⭐⭐⭐⭐ (4 ดาว)" },
          { value: "3", label: "⭐⭐⭐ (3 ดาว)" },
          { value: "2", label: "⭐⭐ (2 ดาว)" },
          { value: "1", label: "⭐ (1 ดาว)" }
        ]
      },
      {
        "key": "comment",
        "label": "ความคิดเห็น",
        "type": "text"
      }
    ]
  }
};

// ---------- สถานะปัจจุบันและฟังก์ชันช่วยเหลือพื้นฐาน ----------
let current = document.querySelector(".tab.active")?.dataset.entity || "customers";   // แท็บที่กำลังเปิดอยู่ (เริ่มที่ตัวแรก = customers)
let editingId = null;                      // id ของแถวที่กำลังแก้ไข (null = กำลังเพิ่มใหม่)
// $ = ทางลัดสำหรับ document.querySelector เพื่อให้เขียนสั้นลง
const $ = (s) => document.querySelector(s);
// แสดงข้อความสถานะใต้ตาราง (cls = "err"/"todo"/"" เพื่อเปลี่ยนสี)
function setStatus(el, msg, cls = "") { el.className = "status " + cls; el.textContent = msg; }
// เรียก API แล้วแปลงผลตอบกลับเป็น JSON อัตโนมัติ
async function api(url, opts) { const res = await fetch(url, opts); return res.json(); }

// ---------- สร้าง HTML ของช่องกรอก 1 ช่อง (ใช้ทั้งช่องค้นหาและช่องในฟอร์ม) ----------
// f = นิยามช่อง, prefix = "s_" (ค้นหา) หรือ "f_" (ฟอร์ม), value = ค่าเริ่มต้น
function fieldHtml(f, prefix, value = "") {
  if (f.type === "heading") return '<div class="form-section">' + f.label + '</div>'; // หัวข้อคั่นกลางฟอร์ม
  let input;
  if (f.key === "phone") {
    input = '<input id="' + prefix + f.key + '" type="tel" inputmode="numeric" maxlength="10" autocomplete="tel"' +
      (prefix === "f_" ? ' minlength="10" pattern="[0-9]{10}" required' : '') + ' value="' + escapeHtml(value ?? "") + '">';
  } else if (f.type === "select") {
    // options เป็นข้อความ "a" หรือ {value, label} ก็ได้
    input = '<select id="' + prefix + f.key + '">' +
      f.options.map(o => {
        const v = typeof o === "object" ? o.value : o;                          // ค่าที่จะส่งไป
        const t = typeof o === "object" ? o.label : (o || "ทั้งหมด");           // ข้อความที่แสดง
        // เทียบค่าปัจจุบัน (value) กับ option นี้ ถ้าตรงกันให้เลือก option นี้ (selected)
        return '<option value="' + escapeHtml(v) + '"' + (String(v) === String(value ?? "") ? " selected" : "") + '>' + escapeHtml(t) + '</option>';
      }).join("") + '</select>';
  } else { input = '<input id="' + prefix + f.key + '" type="' + f.type + '" value="' + escapeHtml(value ?? "") + '">'; }
  if (prefix === "f_" && f.lockOnEdit && editingId !== null) {
    // คู่ item_id และ sub_item_id เป็นคีย์ของแถวคอมโบ จึงล็อกไว้ตอนแก้ไข
    // ผู้ใช้แก้จำนวนและราคาได้ แต่ถ้าต้องการเปลี่ยนคู่เมนู ให้ลบแถวเดิมแล้วเพิ่มคู่ใหม่
    input = input.replace("<select ", "<select disabled ");
  }
  return '<div class="field"><label>' + f.label + '</label>' + input + '</div>';
}
// ช่อง select ที่มี optionsFrom → ดึงตัวเลือกจาก API (เช่น รายชื่อหมวดหมู่จากฐานข้อมูล)
async function loadOptions(fields, forSearch) {
  for (const f of fields.filter(f => f.optionsFrom)) {
    const src = f.optionsFrom, r = await api(src.api);
    // แปลงแถวข้อมูลจาก API เป็น options {value, label} ตามชื่อฟิลด์ที่กำหนด
    f.options = r.ok ? (r.data || []).filter(row => !src.excludeCategory || row.category !== src.excludeCategory).map(row => ({ value: row[src.value], label: row[src.label] }))
                     : [{ value: "", label: (r.todo ? "🚧 " : "⚠️ ") + r.error }];   // ถ้าโหลดไม่ได้ แสดงข้อความ error
    if (!forSearch && r.ok && f.placeholder) f.options.unshift({value:"",label:f.placeholder});
    if (forSearch && r.ok) f.options.unshift({ value: "", label: "ทั้งหมด" });       // ช่องค้นหาเพิ่มตัวเลือก "ทั้งหมด"
  }
}
// ช่องในฟอร์มที่ใช้อยู่ตอนนี้ (ช่อง editOnly แสดงเฉพาะตอนแก้ไข)
function formFields() { return ENTITIES[current].form.filter(f => (!f.editOnly || editingId !== null) && (!f.createOnly || editingId === null)); }

// ---------- สร้างช่องค้นหาตาม ENTITIES ----------
async function buildSearch() {
  const cfg = ENTITIES[current];
  await loadOptions(cfg.search, true);          // โหลดตัวเลือกจาก API ก่อน
  if (cfg !== ENTITIES[current]) return;         // ผู้ใช้เปลี่ยนแท็บระหว่างรอ → ยกเลิก
  $("#searchTitle").textContent = cfg.label;
  $("#btnAdd").hidden = !!cfg.readOnly;
  $("#searchFields").innerHTML = cfg.search.map(f => fieldHtml(f, "s_")).join("");
  bindPhoneInput("s_");  // สร้าง input ทุกช่อง (prefix s_)
}
// ---------- ค้นหา: อ่านค่าจากช่องกรอก แล้วเรียก API ----------
async function doSearch() {
  const cfg = ENTITIES[current];
  const params = new URLSearchParams();
  // ใส่เฉพาะช่องที่กรอกจริงลงเป็น query string เช่น ?name=สม&member_tier=Gold
  cfg.search.forEach(f => { const v = $("#s_" + f.key).value; if (v) params.append(f.key, v); });
  setStatus($("#status"), "กำลังค้นหา...");
  const result = await api(cfg.api + "?" + params.toString());
  if (cfg === ENTITIES[current]) renderTable(result);
}
// ---------- วาดตารางผลลัพธ์ ----------
function renderTable(r) {
  $("#resultTable").dataset.entity = current;
  const head = $("#tableHead");
  const body = $("#tableBody");
  const st = $("#status");

  head.innerHTML = "";
  body.innerHTML = "";

  if (!r.ok) {
    setStatus(
      st,
      (r.todo ? "🚧 " : "⚠️ ") + r.error,
      r.todo ? "todo" : "err"
    );
    return;
  }

  const rows = [...(r.data || [])];

  if (rows.length === 0) {
    setStatus(st, "ไม่พบข้อมูล");
    return;
  }

  // เรียงเวลาสั่งจากเก่าไปใหม่
  if (current === "orders") {
    rows.sort((a, b) =>
      new Date(a.order_time) - new Date(b.order_time) ||
      Number(a.order_id) - Number(b.order_id)
    );
  }

  setStatus(st, "พบ " + rows.length + " รายการ");

  const cols = Object.keys(rows[0]).filter(key => key !== 'receipt_id' && (current !== 'payments' || !['cancel_reason','cancelled_at'].includes(key)));

  head.innerHTML =
    cols.map(c => "<th>" + escapeHtml(COLUMN_LABELS[c] || c) + "</th>").join("") +
    "<th>จัดการ</th>";

  body.innerHTML = rows.map(row => {
    const cfg = ENTITIES[current];
    const id = cfg.idKeys
      ? cfg.idKeys.map(key => row[key])
      : row[cfg.idKey];

    const cells = cols.map(c => {
      let value = row[c] ?? "—";

      // แปลงสถานะในตารางเป็นภาษาไทย
      if (current === "orders" && c === "status") {
        value = ORDER_STATUSES.find(
          s => s.value === row[c]
        )?.label ?? value;
      }

      if (c.endsWith("_time") || c.endsWith("_at")) value = formatRestaurantDate(value);
      if (c === "payment_state") value = value === "PAID" ? "ชำระแล้ว" : "ยกเลิกแล้ว";
      if (c === "payment_status") value = value === "PAID" ? "ชำระแล้ว" : "ยังไม่ชำระ";
      if (c === "zone") value = DINING_ZONES.find(zone => zone.value === value)?.label ?? value;
      if (c === "method") value = value === "CASH" ? "เงินสด" : value === "TRANSFER" ? "โอนเงิน" : value;
      if (current === "payments" && ["subtotal", "discount_amount", "total", "received", "change_amount"].includes(c)) {
        value = Number(value).toLocaleString('th-TH', {minimumFractionDigits:2, maximumFractionDigits:2});
      }
      return "<td>" + escapeHtml(value) + "</td>";
    }).join("");

    const paid = current === "orders" && row.payment_status === "PAID";
    if (current === "payments") {
      return '<tr>' + cells + '<td><button type="button" class="btn sm" onclick="openReceipt(' +
        Number(row.payment_id) + ')">ดูใบเสร็จ</button>' +
        ' <button type="button" class="btn sm del" onclick="deleteReceipt(' + Number(row.payment_id) + ')">ลบ</button>' + '</td></tr>';
    }
    return "<tr>" + cells +
      '<td>' + (current === "orders" ? '<button class="btn sm" onclick="openOrderDetails(' + Number(row.order_id) + ')">รายละเอียด / เช็กบิล</button> ' : '') + (paid ? (row.receipt_id ? '<button type="button" class="btn sm del" onclick="deleteReceipt(' + Number(row.receipt_id) + ')">ลบใบเสร็จ</button>' : '') : '<button class="btn sm" onclick=\'editRow(' +
      JSON.stringify(id) + ')\'>แก้ไข</button> ' +
      '<button class="btn sm del" onclick=\'deleteRow(' +
      JSON.stringify(id) + ')\'>' + (current === "items" ? "เลิกขาย" : "ลบ") + '</button>') + '</td></tr>';
  }).join("");
}
// ประกอบ URL ของทรัพยากร 1 แถว เช่น /api/customers/5 หรือ /api/combos/3/7 (composite key ต่อด้วย /)
function entityUrl(cfg, id) {
  return cfg.api + (id === undefined || id === null ? "" : "/" + (Array.isArray(id) ? id.join("/") : id));
}
// เลือกอาหารหลายรายการ พร้อมจำนวน หมายเหตุ และยอดรวมก่อนบันทึก
let orderMenus = [];
let orderTables = [];
// เก็บราคาตอนสั่งของรายการเดิม เพื่อให้การแก้ไขออเดอร์ไม่ใช้ราคาเมนูใหม่แทนประวัติเดิม
let orderPrices = new Map();
let orderLineIndex = 0;
function escapeHtml(value) {
  // ชื่อเมนูและหมายเหตุอาจมีอักขระพิเศษ จึงแปลงก่อนใส่ HTML เพื่อไม่ให้กลายเป็นแท็กหรือคำสั่ง
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
function buildOrderEditor(items) {
  // items มาจาก API ออเดอร์: ฟอร์มเพิ่มเริ่มด้วยแถวว่าง ส่วนฟอร์มแก้ไขเติมอาหารที่สั่งไว้แล้ว
  orderPrices = new Map(items.map(item => [String(item.item_id), item.unit_price]));
  $("#formFields").insertAdjacentHTML("beforeend", `
    <div class="form-section">สั่งเมนูอาหาร</div>
    <div id="orderLines"></div>
    <button type="button" class="btn add sm" id="btnAddMenu">+ เพิ่มเมนู</button>
    <div class="order-total">ยอดรวม <strong id="orderTotal">0.00</strong> บาท</div>
    <div id="orderError" role="alert" class="order-error"></div>
  `);
  $("#btnAddMenu").onclick = () => addOrderLine();
  (items.length ? items : [{}]).forEach(item => addOrderLine(item));
}
function addOrderLine(item = {}) {
  const line = document.createElement("div");
  line.className = "order-line";
  const index = ++orderLineIndex;
  const available = orderMenus.filter(menu =>
    // เมนูใหม่ต้องพร้อมขายและยังไม่เลิกขาย ส่วนเมนูเก่าในออเดอร์ยังแสดงเพื่อแก้ไขประวัติได้
    (Number(menu.is_available) === 1 && Number(menu.is_discontinued) !== 1) ||
    orderPrices.has(String(menu.item_id))
  );
  const options = available.map(menu => {
    const selected = String(menu.item_id) === String(item.item_id);
    const price = orderPrices.get(String(menu.item_id)) ?? menu.price;
    const suffix = Number(menu.is_available) !== 1 || Number(menu.is_discontinued) === 1
      ? " (ไม่พร้อมขาย)" : "";
    return `<option value="${Number(menu.item_id)}" data-price="${escapeHtml(price)}" ${selected ? "selected" : ""}>${escapeHtml(menu.name)}${suffix} — ${Number(price).toFixed(2)} บาท</option>`;
  }).join("");
  line.innerHTML = `
    <div class="field order-menu-field"><label for="orderMenu${index}">เมนูอาหาร</label>
      <select class="order-menu" id="orderMenu${index}"><option value="">เลือกเมนูอาหาร</option>${options}</select></div>
    <div class="field"><label for="orderQty${index}">จำนวน</label>
      <input class="order-qty" id="orderQty${index}" type="number" min="1" step="1" max="2147483647" value="${escapeHtml(item.qty ?? 1)}"></div>
    <div class="field"><label>รวม (บาท)</label><output class="order-subtotal">0.00</output></div>
    <button type="button" class="btn del sm order-remove" aria-label="ลบรายการอาหาร">ลบ</button>
    <div class="field order-note-field"><label for="orderNote${index}">หมายเหตุอาหาร</label>
      <input class="order-note" id="orderNote${index}" maxlength="255" value="${escapeHtml(item.note)}" placeholder="เช่น ไม่เผ็ด"></div>
  `;
  line.querySelector(".order-menu").onchange = updateOrderTotal;
  line.querySelector(".order-qty").oninput = updateOrderTotal;
  line.querySelector(".order-remove").onclick = () => {line.remove(); updateOrderTotal();};
  $("#orderLines").appendChild(line);
  updateOrderTotal();
}
function updateOrderTotal() {
  // ยอดต่อแถว = ราคาต่อหน่วย × จำนวน และยอดรวม = ผลรวมทุกแถว
  // ตัวเลขบนหน้าเว็บเป็นยอดให้ผู้ใช้ตรวจสอบ ฝั่งเซิร์ฟเวอร์จะอ่านราคาจากฐานข้อมูลอีกครั้งก่อนบันทึก
  let total = 0;
  document.querySelectorAll(".order-line").forEach(line => {
    const selected = line.querySelector(".order-menu").selectedOptions[0];
    const price = Number(selected?.dataset.price || 0);
    const quantity = Number(line.querySelector(".order-qty").value);
    const amount = Number.isFinite(quantity) && quantity > 0 ? price * quantity : 0;
    line.querySelector(".order-subtotal").textContent = amount.toFixed(2);
    total += amount;
  });
  $("#orderTotal").textContent = total.toFixed(2);
}
// ---------- เปิด Modal ฟอร์ม (ใช้ทั้งเพิ่มและแก้ไข) ----------
async function openForm(title, data = {}) {
  const entity = current;
  await loadOptions(formFields(), false);         // โหลดตัวเลือกของช่อง select ที่ดึงจาก API
  if (entity !== current) return;
  if (entity === "orders") {
    const exclude = editingId === null ? "" : "?exclude_order_id=" + encodeURIComponent(editingId);
    const [result, tables] = await Promise.all([api("/api/menu-items"), api("/api/dining-tables" + exclude)]);
    if (entity !== current) return;
    if (!result.ok || !tables.ok) { alert(result.error || tables.error || "โหลดเมนู/โต๊ะไม่สำเร็จ"); return; }
    orderMenus = result.data || [];
    orderTables = tables.data || [];
  }
  $("#modalTitle").textContent = title;
  $("#formFields").innerHTML = formFields().map(f => fieldHtml(f, "f_", data[f.key] ?? f.defaultValue)).join(""); // เติมค่าลงช่อง (prefix f_)
  $(".modal-box").classList.toggle("order-mode", entity === "orders");
  bindPhoneInput("f_");
  if (entity === "orders") {
    bindOrderTables(data.table_id, data.zone);
    buildOrderEditor(data.items || []);
  }
  if (entity === "reviews") {
    document.querySelector("#f_cust_id").onchange = () => loadReviewOrders();
    await loadReviewOrders(data.order_id);
  }
  if (entity !== current) return;
  $("#modal").classList.remove("hidden");         // แสดง Modal
}
// รวบรวมค่าจากทุกช่องในฟอร์มเป็น object เพื่อส่งไป API
function collectForm() {
  // ส่งข้อมูลใบออเดอร์พร้อม items เป็น JSON เช่น {item_id: 1, qty: 2, note: "ไม่เผ็ด"}
  // ไม่ส่ง unit_price ให้ผู้ใช้กำหนดเอง และตรวจจำนวน/เมนูซ้ำก่อนส่งเพื่อลดข้อผิดพลาด
  const data = {};
  formFields().filter(f => f.key).forEach(f => data[f.key] = $("#f_" + f.key).value);
  if (current === "customers" && !/^[0-9]{10}$/.test(data.phone)) throw new Error("กรุณากรอกเบอร์โทรเป็นตัวเลข 10 หลัก");
  if (current === "combos" && editingId === null) {
    const ids=[data.sub_item_id,data.sub_item_id_2,data.sub_item_id_3];
    const amounts=[data.amount,data.amount_2,data.amount_3];
    if (ids.some(id=>!id)) throw new Error("กรุณาเลือกอาหารให้ครบ 3 เมนู");
    if (new Set(ids).size!==3) throw new Error("กรุณาเลือก 3 เมนูที่ไม่ซ้ำกัน");
    if (amounts.some(qty=>!/^[1-9]\d*$/.test(qty))) throw new Error("จำนวนของแต่ละเมนูต้องมากกว่า 0");
    data.items=ids.map((id,index)=>({sub_item_id:id,amount:amounts[index]}));
  }
  if (current === "reviews" && !data.order_id) throw new Error("กรุณาเลือกออเดอร์ที่เสร็จสิ้นของลูกค้า");
  if (current === "orders") {
    const lines = [...document.querySelectorAll(".order-line")];
    if (!data.cust_id || !/^[1-9]\d*$/.test(data.table_id)) {
      throw new Error("กรุณาเลือกลูกค้าและระบุรหัสโต๊ะเป็นจำนวนเต็มมากกว่า 0");
    }
    const selectedTable = orderTables.find(table => String(table.table_id) === data.table_id);
    if (!data.zone || !selectedTable || selectedTable.zone !== data.zone || Number(selectedTable.occupied)) {
      throw new Error("กรุณาเลือกโซนและโต๊ะว่างให้ถูกต้อง");
    }
    if (!lines.length) throw new Error("กรุณาเลือกเมนูอาหารอย่างน้อย 1 รายการ");
    const seen = new Set();
    data.items = lines.map(line => {
      const item_id = line.querySelector(".order-menu").value;
      const qty = line.querySelector(".order-qty").value;
      if (!item_id) throw new Error("กรุณาเลือกเมนูให้ครบทุกรายการ");
      if (!/^[1-9]\d*$/.test(qty) || Number(qty) > 2147483647) {
        throw new Error("จำนวนอาหารต้องเป็นจำนวนเต็มมากกว่า 0");
      }
      if (seen.has(item_id)) throw new Error("เมนูซ้ำกัน กรุณารวมจำนวนในรายการเดียว");
      seen.add(item_id);
      return {item_id, qty, note: line.querySelector(".order-note").value};
    });
  }
  return data;
}
// ---------- ปุ่มแก้ไข: ดึงข้อมูลแถวนั้นมาเติมในฟอร์ม ----------
async function editRow(id) {
  const cfg = ENTITIES[current];
  const r = await api(entityUrl(cfg, id));
  if (!r.ok) { alert((r.todo ? "🚧 " : "⚠️ ") + r.error); return; }
  editingId = id; openForm("แก้ไขข้อมูล", r.data);
}
// ---------- ปุ่มลบ: ยืนยันก่อน แล้วส่ง DELETE ----------
async function deleteRow(id) {
  if (!confirm(current === "items" ? "ยืนยันเลิกขายเมนูนี้? ประวัติและข้อมูลเมนูจะยังคงอยู่" : "ยืนยันการลบ?")) return;
  const r = await api(entityUrl(ENTITIES[current], id), { method: "DELETE" });
  if (!r.ok) { alert((r.todo ? "🚧 " : "⚠️ ") + r.error); return; }
  doSearch();     // ลบเสร็จแล้วโหลดตารางใหม่
}
// ---------- ปุ่มบันทึก: ถ้ากำลังแก้ไข → PUT, ถ้าเพิ่มใหม่ → POST ----------
async function save() {
  // POST ใช้เพิ่มข้อมูลใหม่ ส่วน PUT ใช้แก้ไขข้อมูลเดิมตามรหัสใน URL
  // ปิดปุ่มระหว่างรอ API เพื่อป้องกันการกดซ้ำขณะที่คำขอเดิมยังไม่เสร็จ
  const button = $("#btnSave");
  if (button.disabled) return;
  button.disabled = true;
  try {
    if ($("#orderError")) $("#orderError").textContent = "";
    const cfg = ENTITIES[current], data = collectForm();
    const opts = { method: editingId !== null ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) };
    const r = await api(entityUrl(cfg, editingId), opts);
    if (!r.ok) throw new Error((r.todo ? "🚧 " : "") + r.error);
    $("#modal").classList.add("hidden");
    await doSearch();
  } catch (error) {
    if ($("#orderError")) $("#orderError").textContent = error.message;
    else alert(error.message);
  } finally {
    button.disabled = false;
  }
}
// ---------- ผูก Event ให้ปุ่ม/แท็บต่าง ๆ ----------
// คลิกแท็บ → เปลี่ยน entity แล้วสร้างช่องค้นหาใหม่ + ล้างตารางเดิม
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
  t.classList.add("active"); current = t.dataset.entity;
  buildSearch(); $("#tableHead").innerHTML = ""; $("#tableBody").innerHTML = "";
  setStatus($("#status"), 'กด "ค้นหา" เพื่อแสดงข้อมูล');
}));
$("#btnSearch").onclick = doSearch;                                             // ค้นหา
$("#btnClear").onclick = () => buildSearch();                                   // ล้างเงื่อนไขค้นหา
$("#btnAdd").onclick = () => { editingId = null; openForm("เพิ่มข้อมูลใหม่"); }; // เพิ่มข้อมูลใหม่
$("#btnSave").onclick = save;                                                  // บันทึก
$("#btnCancel").onclick = () => $("#modal").classList.add("hidden");            // ยกเลิก / ปิด Modal
buildSearch();                                                                  // สร้างช่องค้นหาครั้งแรก
setStatus($("#status"), 'กด "ค้นหา" เพื่อแสดงข้อมูล');


// เมื่อเปลี่ยนลูกค้า จะล้างออเดอร์เก่า และโหลดเฉพาะออเดอร์ COMPLETED ของคนนั้น
let reviewOptionsRequest = 0;
async function loadReviewOrders(selectedId = "") {
  const requestId = ++reviewOptionsRequest;
  const customer = document.querySelector("#f_cust_id");
  const select = document.querySelector("#f_order_id");
  if (!customer || !select) return;
  const custId = customer.value;
  select.disabled = true;
  select.innerHTML = '<option value="">กำลังโหลดออเดอร์…</option>';
  try {
    const result = await api('/api/orders?cust_id=' + encodeURIComponent(custId) + '&status=COMPLETED');
    if (requestId !== reviewOptionsRequest || current !== "reviews" || customer.value !== custId || !select.isConnected) return;
    if (!result.ok) throw new Error(result.error || "โหลดออเดอร์ไม่สำเร็จ");
    const orders = (result.data || []).filter(order => String(order.cust_id) === custId && order.status === 'COMPLETED');
    select.innerHTML = '<option value="">' + (orders.length ? 'เลือกออเดอร์' : 'ลูกค้าคนนี้ยังไม่มีออเดอร์ที่เสร็จสิ้น') + '</option>' +
      orders.map(order => '<option value="' + Number(order.order_id) + '"' +
        (String(order.order_id) === String(selectedId) ? ' selected' : '') + '>#' + Number(order.order_id) +
        ' · ' + escapeHtml(formatRestaurantDate(order.order_time)) + '</option>').join('');
  } catch (error) {
    if (requestId === reviewOptionsRequest && select.isConnected) select.innerHTML = '<option value="">' + escapeHtml(error.message) + '</option>';
  } finally {
    if (requestId === reviewOptionsRequest && select.isConnected) select.disabled = false;
  }
}


function bindPhoneInput(prefix) {
  const input = document.querySelector("#" + prefix + "phone");
  if (!input) return;
  // จำกัดเฉพาะเลข 0–9 โดยคงเลข 0 นำหน้าไว้ และรับได้ไม่เกิน 10 หลัก
  input.oninput = () => {input.value = input.value.replace(/[^0-9]/g, "").slice(0, 10);};
  input.onpaste = event => {
    const text = event.clipboardData?.getData("text");
    if (text === undefined) return;
    event.preventDefault();
    const digits = text.replace(/[^0-9]/g, "");
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? start;
    input.value = (input.value.slice(0,start) + digits + input.value.slice(end)).slice(0,10);
    const cursor = Math.min(start + digits.length,10);
    input.setSelectionRange(cursor,cursor);
  };
}

function bindOrderTables(selectedId, selectedZone) {
  const zone = document.querySelector("#f_zone");
  const select = document.querySelector("#f_table_id");
  const existing = orderTables.find(table => String(table.table_id) === String(selectedId));
  zone.value = existing?.zone || selectedZone || "";
  const render = id => {
    const tables = orderTables.filter(table => table.zone === zone.value && Number(table.occupied) === 0);
    const prompt = !zone.value ? "เลือกโซนก่อน" : tables.length ? "เลือกโต๊ะว่าง" : "ไม่มีโต๊ะว่างในโซนนี้";
    select.innerHTML = '<option value="">' + prompt + '</option>' + tables.map(table =>
      '<option value="' + Number(table.table_id) + '"' +
      (String(table.table_id) === String(id) ? ' selected' : '') +
      '>โต๊ะ ' + Number(table.table_id) + ' · ' +
      Number(table.seats) + ' ที่นั่ง (ว่าง)' + '</option>'
    ).join('');
    select.disabled = !zone.value || !tables.length;
  };
  zone.onchange = () => render("");
  render(selectedId);
}
