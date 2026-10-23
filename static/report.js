// ============================================================
//  report.js  —  ตรรกะหน้ารายงาน (ทำให้เสร็จแล้ว ★)
//  หน้าที่: 1) ดึงตัวเลขสรุปมาแสดงเป็นการ์ด  2) สร้างตารางรายงานทุกตัวให้อัตโนมัติ
// ============================================================
const $ = (s) => document.querySelector(s);         // ทางลัด querySelector
async function api(url) { return (await fetch(url)).json(); }   // เรียก API แล้วคืน JSON
// ข้อความรีวิว/ชื่อลูกค้ามาจากผู้ใช้ จึงต้องแปลงอักขระก่อนสร้าง HTML ของรายงาน
function reportEscape(value) {
  return String(value ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function reportValue(value) {
  const text=String(value ?? "—");
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const date=new Date(text.replace(' ','T'));
    if (Number.isFinite(date.getTime())) return new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
      day:'2-digit',month:'2-digit',year:'numeric',...(text.length>10 ? {hour:'2-digit',minute:'2-digit',hourCycle:'h23'} : {})
    }).format(date);
  }
  return text;
}

// วาดข้อมูลลงตาราง: tableSel = ตารางเป้าหมาย, statusSel = จุดแสดงข้อความสถานะ, r = JSON ที่ได้จาก API
function fillTable(tableSel, statusSel, r) {
  const t = $(tableSel), st = $(statusSel);
  const thead = t.querySelector("thead"), tbody = t.querySelector("tbody");
  thead.innerHTML = ""; tbody.innerHTML = "";           // ล้างของเก่าก่อนวาดใหม่
  if (!r.ok) { st.className = "status " + (r.todo ? "todo" : "err"); st.textContent = (r.todo ? "🚧 " : "⚠️ ") + r.error; return; }
  const rows = r.data || [];
  if (!rows.length) { st.className = "status"; st.textContent = "ไม่มีข้อมูล"; return; }
  st.textContent = "";
  const cols = Object.keys(rows[0]);                     // ชื่อคอลัมน์ = กุญแจของแถวแรก (มาจาก SQL alias)
  thead.innerHTML = "<tr>" + cols.map(c => "<th>" + reportEscape(c) + "</th>").join("") + "</tr>";
  tbody.innerHTML = rows.map(row => "<tr>" + cols.map(c => "<td>" + reportEscape(reportValue(row[c])) + "</td>").join("") + "</tr>").join("");
}
// ---------- โหลดตัวเลขสรุปมาแสดงเป็นการ์ดด้านบน ----------
async function loadSummary() {
  // report_summary() คืน dict {ชื่อการ์ด: ตัวเลข} → 1 คีย์ = 1 การ์ด
  const r = await api("/api/reports/summary");
  const box = $("#summary");
  if (!r.ok) { box.innerHTML = '<div style="grid-column:1/-1" class="status ' + (r.todo ? "todo" : "err") + '">' + (r.todo ? "🚧 " : "⚠️ ") + r.error + '</div>'; return; }
  // Object.entries แตก dict เป็นคู่ [label, num] แล้วสร้างการ์ดทีละใบ
  box.innerHTML = Object.entries(r.data || {}).map(([label, num]) =>
    '<div class="metric"><div class="metric-num">' + reportEscape(num) + '</div><div class="metric-label">' + reportEscape(label) + '</div></div>').join("");
}
// ---------- โหลดรายงานทั้งหมด ----------
async function loadAll() {
  loadSummary();   // เริ่มจากการ์ดสรุปก่อน
  // สร้างกล่องรายงานตามรายการ REPORTS ใน db.py
  const list = await api("/api/reports");
  for (const rep of (list.data || [])) {
    const id = "rep_" + rep.key.replace(/\W/g, "_");   // แปลง key เป็น id ที่ใช้ใน HTML ได้ (อักขระพิเศษ → _)
    const sec = document.createElement("section");
    sec.className = "card";
    // สร้างการ์ด + ตารางว่างของรายงานแต่ละตัว
    sec.innerHTML = '<h3>' + rep.title + '</h3><div id="' + id + '_status" class="status"></div>' +
      '<div class="table-wrap"><table id="' + id + '_table"><thead></thead><tbody></tbody></table></div>';
    $("#reports").appendChild(sec);
    // เรียก API ของรายงาน key นี้ แล้ววาดผลลงตาราง
    fillTable("#" + id + "_table", "#" + id + "_status", await api("/api/reports/" + rep.key));
  }
}
loadAll();   // เริ่มทำงานเมื่อเปิดหน้า /report
