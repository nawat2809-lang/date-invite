# หน้าเว็บขอจีบ ♡ (มายเมโรดี้)

เว็บ static ล้วน ไฟล์เดียวจบ ไม่ต้อง build ไม่ต้องติดตั้งอะไร — ใช้ HTML + CSS + JS ในไฟล์เดียว

## ไฟล์ที่มี
| ไฟล์ | คำอธิบาย |
| --- | --- |
| `index.html` | เวอร์ชันแรก (ธีมหวานละมุน) |
| `index-mymelody.html` | เวอร์ชันใหม่ ธีมมายเมโรดี้ — ตัวการ์ตูนวาดด้วย SVG + อนิเมชัน |
| `.nojekyll` | บอก GitHub Pages ว่าไม่ต้องประมวลผลด้วย Jekyll |

## เปิดดูในเครื่อง
- ดับเบิลคลิกไฟล์ `.html` เปิดด้วยเบราว์เซอร์ได้เลย หรือ
- รันเซิร์ฟเวอร์ท้องถิ่น: `python -m http.server 8123 --bind 127.0.0.1` แล้วเปิด `http://127.0.0.1:8123/index-mymelody.html`

## ขึ้น GitHub Pages
1. สร้าง repository ใหม่บน GitHub (เลือก Public) เช่นชื่อ `love-surprise`
2. ผูก remote แล้ว push:
   ```bash
   git remote add origin https://github.com/<ชื่อผู้ใช้>/<ชื่อ-repo>.git
   git push -u origin main
   ```
3. ไปที่ repo → **Settings → Pages**
4. **Source** เลือก `Deploy from a branch`, **Branch** เลือก `main` และโฟลเดอร์ `/ (root)` → **Save**
5. รอ 1–2 นาที จะได้ลิงก์:
   - `https://<ชื่อผู้ใช้>.github.io/<ชื่อ-repo>/index-mymelody.html` (เวอร์ชันมายเมโรดี้)
   - `https://<ชื่อผู้ใช้>.github.io/<ชื่อ-repo>/` (เวอร์ชันแรก)

### อยากให้หน้าแรกของเว็บเป็นเวอร์ชันมายเมโรดี้
เปลี่ยนชื่อไฟล์เป็น `index.html` (เก็บของเดิมไว้เป็น `index-v1.html` ก็ได้) แล้ว commit + push ใหม่
