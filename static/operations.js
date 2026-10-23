/* งานหน้าร้านใช้ข้อมูลจากเซิร์ฟเวอร์; ตัวเลขที่หน้าเว็บคำนวณใช้แสดงตัวอย่างเท่านั้น */
window.COLUMN_LABELS = Object.freeze({
  cust_id:'รหัสลูกค้า', name:'ชื่อ', phone:'เบอร์โทร', member_tier:'ระดับสมาชิก',
  item_id:'รหัสเมนู', category:'หมวดหมู่', price:'ราคา', is_available:'พร้อมขาย', is_discontinued:'เลิกขาย',
  combo_name:'ชื่อชุด', sub_item_id:'รหัสเมนูย่อย', sub_item_name:'เมนูในชุด', amount:'จำนวนในชุด', combo_price:'ราคาชุด',
  zone:'โซนที่นั่ง', seats:'จำนวนที่นั่ง', order_id:'ออเดอร์', customer_name:'ลูกค้า', table_id:'โต๊ะ', order_time:'เวลาสั่ง', status:'สถานะอาหาร',
  total:'ยอดรวม', payment_status:'การชำระเงิน', review_id:'รหัสรีวิว', rating:'คะแนน', comment:'ความคิดเห็น', review_time:'วันที่รีวิว',
  payment_state:'สถานะบิล', cancel_reason:'เหตุผลยกเลิก', cancelled_at:'วันที่ยกเลิก', payment_id:'เลขใบเสร็จ', method:'วิธีชำระ', subtotal:'ก่อนส่วนลด', discount_amount:'ส่วนลด',
  received:'รับเงิน', change_amount:'เงินทอน', payment_time:'วันที่ชำระ'
});
function formatRestaurantDate(value) {
  if (!value || value === '—') return '—';
  const date = new Date(String(value).replace(' ', 'T'));
  if (!Number.isFinite(date.getTime())) return String(value);
  return new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
    day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'
  }).format(date);
}
(function () {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const cash = value => Number(value || 0).toLocaleString('th-TH',{minimumFractionDigits:2,maximumFractionDigits:2});
  const zoneLabel = value => ({INDOOR:'ในร้าน',OUTDOOR:'นอกร้าน',VIP:'VIP'}[value] || value || '');
  const statuses = {PENDING:'รอดำเนินการ',IN_PROGRESS:'กำลังทำ',READY:'พร้อมเสิร์ฟ',COMPLETED:'เสิร์ฟครบแล้ว',CANCELLED:'ยกเลิก'};
  let detailRequest = 0;
  let paying = false;
  const request = async (url, data) => {
    const response = await fetch(url, data === undefined ? undefined : {
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)
    });
    let result;
    try { result = await response.json(); } catch (_) { throw new Error('อ่านข้อมูลจากเซิร์ฟเวอร์ไม่ได้ กรุณาลองใหม่'); }
    if (!response.ok || !result.ok) throw new Error(result.error || 'ดำเนินการไม่สำเร็จ');
    return result.data;
  };
  const errorText = (box, error) => {box.textContent=error.message; box.classList.add('err');};
  function modal() {
    let overlay = document.querySelector('#serviceModal');
    if (!overlay) {
      overlay=document.createElement('div');
      overlay.id='serviceModal'; overlay.className='modal hidden';
      overlay.innerHTML='<section class="modal-box service-dialog" role="dialog" aria-modal="true" aria-labelledby="serviceTitle"><button class="btn sm dialog-close" id="serviceClose" aria-label="ปิดรายละเอียด">ปิด</button><div id="serviceContent"></div></section>';
      document.body.appendChild(overlay);
      overlay.querySelector('#serviceClose').onclick=()=>{
        if (paying) return;
        ++detailRequest; overlay.classList.add('hidden');
      };
    }
    return overlay;
  }
  window.openOrderDetails = async orderId => {
    const id = Number(orderId);
    const version = ++detailRequest;
    const overlay=modal();
    const content=overlay.querySelector('#serviceContent');
    overlay.classList.remove('hidden');
    content.innerHTML='<h2 id="serviceTitle">รายละเอียดออเดอร์</h2><p class="status">กำลังโหลด…</p>';
    try {
      const order=await request('/api/orders/'+id+'/details');
      if (version!==detailRequest) return;
      const items=order.items || [];
      const bill=order.bill;
      content.innerHTML=`<h2 id="serviceTitle">ออเดอร์ #${id}</h2>
        <p class="service-muted">โต๊ะ ${Number(order.table_id)}${order.zone ? " · โซน " + esc(zoneLabel(order.zone)) : ""} · ${esc(order.customer_name)} · ${esc(order.member_tier)}<br>${esc(formatRestaurantDate(order.order_time))}</p>
        <span class="state-pill ${esc(order.status)}">${esc(statuses[order.status] || order.status)}</span>
        <div class="table-wrap service-lines"><table><thead><tr><th>รายการอาหาร</th><th>จำนวน</th><th>ราคาต่อหน่วย</th><th>รวม</th></tr></thead><tbody>
          ${items.map(item=>`<tr><td>${esc(item.name)}${item.note ? '<small class="item-note">'+esc(item.note)+'</small>' : ''}</td><td>${Number(item.qty)}</td><td>${cash(item.unit_price)}</td><td>${cash(Number(item.qty)*Number(item.unit_price))}</td></tr>`).join('')}
        </tbody></table></div>
        <div class="bill-summary"><p>มูลค่าอาหาร <strong>${cash(bill.subtotal)} บาท</strong></p></div>
        <div id="checkoutSection"></div><p id="checkoutError" class="status" role="alert"></p>`;
      const checkoutSection=content.querySelector('#checkoutSection');
      if (order.payment) {
        checkoutSection.innerHTML=`<div class="paid-banner">ชำระแล้ว ${cash(order.payment.total)} บาท · ${esc(formatRestaurantDate(order.payment.payment_time))}</div>
          `;
      } else if (order.status==='COMPLETED' && items.length) {
        checkoutSection.innerHTML=`<div class="checkout-box"><h3>เช็กบิล</h3>
          <p>ส่วนลดสมาชิก ${esc(order.member_tier)} ${cash(bill.discount_rate)}% <strong>−${cash(bill.discount_amount)} บาท</strong></p>
          <p class="net-total">ยอดชำระ <strong>${cash(bill.total)} บาท</strong></p>
          <div class="search-grid"><div class="field"><label for="payMethod">วิธีชำระ</label><select id="payMethod"><option value="CASH">เงินสด</option><option value="TRANSFER">โอนเงิน</option></select></div>
          <div class="field"><label for="payReceived">จำนวนเงินที่รับ (บาท)</label><input type="number" id="payReceived" min="${Number(bill.total)}" step="0.01" value="${Number(bill.total).toFixed(2)}"></div></div>
          <p id="changePreview" class="service-muted"></p><p class="service-muted">กดยืนยันเมื่อได้รับเงินแล้ว การโอนให้พนักงานตรวจยอดรับก่อน</p>
          <button type="button" class="btn add" id="confirmPayment">ยืนยันรับชำระเงิน</button></div>`;
        const method=content.querySelector('#payMethod'), received=content.querySelector('#payReceived');
        const showChange=()=>{
          const transferred=method.value==='TRANSFER';
          received.readOnly=transferred;
          if (transferred) received.value=Number(bill.total).toFixed(2);
          const change=Number(received.value)-Number(bill.total);
          content.querySelector('#changePreview').textContent=Number.isFinite(change) && change>=0 ? 'เงินทอน '+cash(change)+' บาท' : 'จำนวนเงินที่รับยังไม่ครบ';
        };
        method.onchange=showChange; received.oninput=showChange; showChange();
        content.querySelector('#confirmPayment').onclick=async()=>{
          if (paying || !received.reportValidity()) return;
          if (!window.confirm('ยืนยันว่าได้รับเงิน '+cash(received.value)+' บาทแล้ว?')) return;
          const button=content.querySelector('#confirmPayment');
          paying=true; button.disabled=true; overlay.querySelector('#serviceClose').disabled=true;
          try {
            const payment=await request('/api/orders/'+id+'/checkout', {
              method:method.value,received:received.value,expected_total:String(bill.total)
            });
            checkoutSection.innerHTML=`<div class="paid-banner" role="status">รับชำระเรียบร้อย · เงินทอน ${cash(payment.change_amount)} บาท</div>`;
            if (typeof window.doSearch==='function' && document.querySelector('.tab.active')?.dataset.entity==='orders') await window.doSearch();
          } catch(error) {errorText(content.querySelector('#checkoutError'),error); button.disabled=false;}
          finally {paying=false; overlay.querySelector('#serviceClose').disabled=false;}
        };
      } else {
        checkoutSection.innerHTML='<p class="service-muted">'+(order.status==='CANCELLED' ? 'ออเดอร์ยกเลิกแล้ว' : 'เช็กบิลได้เมื่อเสิร์ฟอาหารครบแล้ว')+'</p>';
      }
    } catch(error) {
      if (version===detailRequest) content.innerHTML='<h2 id="serviceTitle">รายละเอียดออเดอร์</h2><p class="status err">'+esc(error.message)+'</p>';
    }
  };

  // ใบเสร็จแสดงใน modal เดิม แต่ใช้ snapshot ที่บันทึกตอนจ่ายเสมอ
  window.openReceipt = async paymentId => {
    if (paying) return;
    const id=Number(paymentId);
    const version=++detailRequest;
    const overlay=modal();
    const content=overlay.querySelector('#serviceContent');
    overlay.classList.remove('hidden');
    content.innerHTML='<h2 id="serviceTitle">ใบเสร็จรับเงิน</h2><p class="status">กำลังโหลด…</p>';
    try {
      const receipt=await request('/api/payments/'+id+'/receipt');
      if (version!==detailRequest) return;
      const snapshot=receipt.snapshot;
      content.innerHTML=`<h2 id="serviceTitle">ใบเสร็จรับเงิน #${id}</h2>
        <p class="service-muted">ออเดอร์ #${Number(receipt.order_id)} · โต๊ะ ${Number(snapshot.table_id)}${snapshot.zone ? " · โซน " + esc(zoneLabel(snapshot.zone)) : ""}<br>
          ${esc(snapshot.customer_name)} · ${esc(receipt.member_tier)}<br>
          วันที่ชำระ ${esc(formatRestaurantDate(receipt.payment_time))}</p>
        <div class="table-wrap service-lines"><table><thead><tr><th>รายการอาหาร</th><th>จำนวน</th><th>ราคาต่อหน่วย</th><th>รวม</th></tr></thead><tbody>
          ${snapshot.items.map(item=>`<tr><td>${esc(item.name)}${item.note ? '<small class="item-note">'+esc(item.note)+'</small>' : ''}</td><td>${Number(item.qty)}</td><td>${cash(item.unit_price)}</td><td>${cash(item.line_total)}</td></tr>`).join('')}
        </tbody></table></div>
        <div class="bill-summary">
          <p>มูลค่าอาหาร <strong>${cash(receipt.subtotal)} บาท</strong></p>
          <p>ส่วนลดสมาชิก ${esc(receipt.member_tier)} ${cash(receipt.discount_rate)}% <strong>−${cash(receipt.discount_amount)} บาท</strong></p>
          <p class="net-total">ชำระสุทธิ <strong>${cash(receipt.total)} บาท</strong></p>
          <p>วิธีชำระ <strong>${receipt.method==='CASH' ? 'เงินสด' : 'โอนเงิน'}</strong></p>
          <p>รับเงิน <strong>${cash(receipt.received)} บาท</strong></p>
          <p>เงินทอน <strong>${cash(receipt.change_amount)} บาท</strong></p>
        </div>${receipt.status === 'CANCELLED'
          ? `<div class="status err"><strong>ยกเลิกบิลแล้ว</strong><br>เหตุผล: ${esc(receipt.cancel_reason)}<br>วันที่ยกเลิก ${esc(formatRestaurantDate(receipt.cancelled_at))}</div><button type="button" class="btn" onclick="openOrderDetails(${Number(receipt.order_id)})">ดูออเดอร์ / รับชำระใหม่</button>`
          : `<div class="paid-banner">ชำระแล้ว ${cash(receipt.total)} บาท · ${esc(formatRestaurantDate(receipt.payment_time))}</div>`}
        <div id="cancelPaymentSection"></div>`;

    } catch (error) {
      if (version===detailRequest) content.innerHTML='<h2 id="serviceTitle">ใบเสร็จรับเงิน</h2><p class="status err" role="alert">'+esc(error.message)+'</p>';
    }
  };
  window.deleteReceipt = async paymentId => {
    if (paying) return;
    const id=Number(paymentId);
    if (!window.confirm('ลบใบเสร็จ #'+id+' ออกจากรายการ? สถานะชำระเงินและยอดรับเงินจะคงเดิม')) return;
    paying=true;
    const buttons=[...document.querySelectorAll('#tableBody button')];
    buttons.forEach(button=>button.disabled=true);
    let deleted=false;
    try {
      await request('/api/payments/'+id+'/delete-receipt',{});
      deleted=true;
    } catch(error) {errorText(document.querySelector('#status'),error);}
    finally {paying=false;buttons.forEach(button=>button.disabled=false);}
    if (deleted) {
      // อยู่หน้าใบเสร็จและใช้เงื่อนไขค้นหาเดิม ไม่เปลี่ยนออเดอร์กลับเป็นยังไม่ชำระ
      if (['payments','orders'].includes(document.querySelector('.tab.active')?.dataset.entity)) {
        try {await window.doSearch();}
        catch (_) {document.querySelector('#status').textContent='ลบแล้ว กรุณากดค้นหาเพื่อโหลดรายการใหม่';}
      }
    }
  };
})();
