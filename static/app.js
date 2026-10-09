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
const ITEM_CATEGORIES = [
  { value: "อาหารเรียกน้ำย่อย", label: "อาหารเรียกน้ำย่อย" },
  { value: "อาหารจานหลัก", label: "อาหารจานหลัก" },
  { value: "ของหวาน", label: "ของหวาน" },
  { value: "เครื่องดื่ม", label: "เครื่องดื่ม" },
  { value: "ชุดคอมโบ", label: "ชุดคอมโบ" }
];
// สถานะของออเดอร์ (ค่าตรงกับ ENUM ในฐานข้อมูล) — value คือค่าที่ส่งไป API, label คือข้อความที่ผู้ใช้เห็น
const ORDER_STATUSES = [
  { value: "PENDING", label: "PENDING (รอดำเนินการ)" },
  { value: "IN_PROGRESS", label: "IN_PROGRESS (กำลังดำเนินการ)" },
  { value: "COMPLETED", label: "COMPLETED (เสร็จสิ้น)" },
  { value: "CANCELLED", label: "CANCELLED (ยกเลิก)" }
];

// ENTITIES = ศูนย์กลางการตั้งค่าของทั้งหน้าเว็บ: แต่ละ entity บอก label, api, คีย์หลัก, ช่องค้นหา (search) และช่องฟอร์ม (form)
const ENTITIES = {
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
        "label": "ระดับ",
        "type": "select",
        "options": [
          "Regular",
          "Gold",
          "VIP"
        ]
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
          { value: "0", label: "ไม่พร้อมขาย" }
        ]
      }
    ]
  },
  // ---------- ชุดคอมโบ (combos) ----------
  "combos": {
    "label": "ชุดคอมโบ",
    "api": "/api/combos",
    // คีย์หลักมี 2 ตัว (composite key) จึงใช้ idKeys แทน idKey
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
        "key": "item_id",
        "label": "เมนูชุดหลัก",
        "type": "select",
        "editOnly": true,
        "optionsFrom": {
          "api": "/api/menu-items",
          "value": "item_id",
          "label": "name"
        }
      },
      {
        "key": "sub_item_id",
        "label": "เมนูที่อยู่ในชุด",
        "type": "select",
        "editOnly": true,
        "optionsFrom": {
          "api": "/api/menu-items",
          "value": "item_id",
          "label": "name"
        }
      },
      {
        "key": "amount",
        "label": "จำนวน",
        "type": "number"
      },
      {
        "key": "price",
        "label": "ราคาเซ็ต",
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
      {
        "key": "table_id",
        "label": "รหัสโต๊ะ",
        "type": "number"
      },
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
        "label": "รหัสออเดอร์",
        "type": "number"
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
let current = Object.keys(ENTITIES)[0];   // แท็บที่กำลังเปิดอยู่ (เริ่มที่ตัวแรก = customers)
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
  if (f.type === "select") {
    // options เป็นข้อความ "a" หรือ {value, label} ก็ได้
    input = '<select id="' + prefix + f.key + '">' +
      f.options.map(o => {
        const v = typeof o === "object" ? o.value : o;                          // ค่าที่จะส่งไป
        const t = typeof o === "object" ? o.label : (o || "ทั้งหมด");           // ข้อความที่แสดง
        // เทียบค่าปัจจุบัน (value) กับ option นี้ ถ้าตรงกันให้เลือก option นี้ (selected)
        return '<option value="' + v + '"' + (String(v) === String(value ?? "") ? " selected" : "") + '>' + t + '</option>';
      }).join("") + '</select>';
  } else { input = '<input id="' + prefix + f.key + '" type="' + f.type + '" value="' + (value ?? "") + '">'; }
  return '<div class="field"><label>' + f.label + '</label>' + input + '</div>';
}
// ช่อง select ที่มี optionsFrom → ดึงตัวเลือกจาก API (เช่น รายชื่อหมวดหมู่จากฐานข้อมูล)
async function loadOptions(fields, forSearch) {
  for (const f of fields.filter(f => f.optionsFrom)) {
    const src = f.optionsFrom, r = await api(src.api);
    // แปลงแถวข้อมูลจาก API เป็น options {value, label} ตามชื่อฟิลด์ที่กำหนด
    f.options = r.ok ? (r.data || []).map(row => ({ value: row[src.value], label: row[src.label] }))
                     : [{ value: "", label: (r.todo ? "🚧 " : "⚠️ ") + r.error }];   // ถ้าโหลดไม่ได้ แสดงข้อความ error
    if (forSearch && r.ok) f.options.unshift({ value: "", label: "ทั้งหมด" });       // ช่องค้นหาเพิ่มตัวเลือก "ทั้งหมด"
  }
}
// ช่องในฟอร์มที่ใช้อยู่ตอนนี้ (ช่อง editOnly แสดงเฉพาะตอนแก้ไข)
function formFields() { return ENTITIES[current].form.filter(f => !f.editOnly || editingId !== null); }

// ---------- สร้างช่องค้นหาตาม ENTITIES ----------
async function buildSearch() {
  const cfg = ENTITIES[current];
  await loadOptions(cfg.search, true);          // โหลดตัวเลือกจาก API ก่อน
  if (cfg !== ENTITIES[current]) return;         // ผู้ใช้เปลี่ยนแท็บระหว่างรอ → ยกเลิก
  $("#searchTitle").textContent = cfg.label;
  $("#searchFields").innerHTML = cfg.search.map(f => fieldHtml(f, "s_")).join("");  // สร้าง input ทุกช่อง (prefix s_)
}
// ---------- ค้นหา: อ่านค่าจากช่องกรอก แล้วเรียก API ----------
async function doSearch() {
  const cfg = ENTITIES[current];
  const params = new URLSearchParams();
  // ใส่เฉพาะช่องที่กรอกจริงลงเป็น query string เช่น ?name=สม&member_tier=Gold
  cfg.search.forEach(f => { const v = $("#s_" + f.key).value; if (v) params.append(f.key, v); });
  setStatus($("#status"), "กำลังค้นหา...");
  renderTable(await api(cfg.api + "?" + params.toString()));
}
// ---------- วาดตารางผลลัพธ์ ----------
function renderTable(r) {
  const head = $("#tableHead"), body = $("#tableBody"), st = $("#status");
  head.innerHTML = ""; body.innerHTML = "";
  if (!r.ok) { setStatus(st, (r.todo ? "🚧 " : "⚠️ ") + r.error, r.todo ? "todo" : "err"); return; }
  const rows = r.data || [];
  if (rows.length === 0) { setStatus(st, "ไม่พบข้อมูล"); return; }
  setStatus(st, "พบ " + rows.length + " รายการ");
  const cols = Object.keys(rows[0]);   // ชื่อคอลัมน์ดึงจากกุญแจของแถวแรก (ตรงกับ SQL SELECT)
  head.innerHTML = cols.map(c => "<th>" + c + "</th>").join("") + "<th>จัดการ</th>";
  body.innerHTML = rows.map(row => {
    const cfg = ENTITIES[current];
    // id ของแถว: composite key (idKeys) หรือ id เดียว (idKey) แล้วส่งต่อไปยังปุ่มแก้ไข/ลบ
    const id = cfg.idKeys ? cfg.idKeys.map(key => row[key]) : row[cfg.idKey];
    return "<tr>" + cols.map(c => "<td>" + (row[c] ?? "—") + "</td>").join("") +
      '<td><button class="btn sm" onclick=\'editRow(' + JSON.stringify(id) + ')\'>แก้ไข</button> ' +
      '<button class="btn sm del" onclick=\'deleteRow(' + JSON.stringify(id) + ')\'>ลบ</button></td></tr>';
  }).join("");
}
// ประกอบ URL ของทรัพยากร 1 แถว เช่น /api/customers/5 หรือ /api/combos/3/7 (composite key ต่อด้วย /)
function entityUrl(cfg, id) {
  return cfg.api + (id === undefined || id === null ? "" : "/" + (Array.isArray(id) ? id.join("/") : id));
}
// ---------- เปิด Modal ฟอร์ม (ใช้ทั้งเพิ่มและแก้ไข) ----------
async function openForm(title, data = {}) {
  await loadOptions(formFields(), false);         // โหลดตัวเลือกของช่อง select ที่ดึงจาก API
  $("#modalTitle").textContent = title;
  $("#formFields").innerHTML = formFields().map(f => fieldHtml(f, "f_", data[f.key])).join(""); // เติมค่าลงช่อง (prefix f_)
  $("#modal").classList.remove("hidden");         // แสดง Modal
}
// รวบรวมค่าจากทุกช่องในฟอร์มเป็น object เพื่อส่งไป API
function collectForm() { const d = {}; formFields().filter(f => f.key).forEach(f => d[f.key] = $("#f_" + f.key).value); return d; }
// ---------- ปุ่มแก้ไข: ดึงข้อมูลแถวนั้นมาเติมในฟอร์ม ----------
async function editRow(id) {
  const cfg = ENTITIES[current];
  const r = await api(entityUrl(cfg, id));
  if (!r.ok) { alert((r.todo ? "🚧 " : "⚠️ ") + r.error); return; }
  editingId = id; openForm("แก้ไขข้อมูล", r.data);
}
// ---------- ปุ่มลบ: ยืนยันก่อน แล้วส่ง DELETE ----------
async function deleteRow(id) {
  if (!confirm("ยืนยันการลบ?")) return;
  const r = await api(entityUrl(ENTITIES[current], id), { method: "DELETE" });
  if (!r.ok) { alert((r.todo ? "🚧 " : "⚠️ ") + r.error); return; }
  doSearch();     // ลบเสร็จแล้วโหลดตารางใหม่
}
// ---------- ปุ่มบันทึก: ถ้ากำลังแก้ไข → PUT, ถ้าเพิ่มใหม่ → POST ----------
async function save() {
  const cfg = ENTITIES[current], data = collectForm();
  const opts = { method: editingId ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) };
  const r = await api(entityUrl(cfg, editingId), opts);
  if (!r.ok) { alert((r.todo ? "🚧 " : "⚠️ ") + r.error); return; }
  $("#modal").classList.add("hidden"); doSearch();   // ปิด Modal แล้วโหลดตารางใหม่
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
