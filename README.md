# หน้าเว็บขอจีบ ♡ (มายเมโรดี้)

เว็บ static ล้วน ไฟล์เดียวจบ ไม่ต้อง build ไม่ต้องติดตั้งอะไร — ใช้ HTML + CSS + JS ในไฟล์เดียว

## ลิงก์เว็บ
- https://nawat2809-lang.github.io/date-invite/ — หน้าแรก (เวอร์ชันมายเมโรดี้)
- https://nawat2809-lang.github.io/date-invite/index-v1.html — เวอร์ชันแรก

## ไฟล์ที่มี
| ไฟล์ | คำอธิบาย |
| --- | --- |
| `index.html` | หน้าแรกของเว็บ = เวอร์ชันมายเมโรดี้ (ตัวการ์ตูน SVG + อนิเมชัน) |
| `index-mymelody.html` | ไฟล์เดียวกัน ใช้เป็นลิงก์ตรงได้ |
| `index-v1.html` | เวอร์ชันแรก (ธีมหวานละมุน) |
| `.nojekyll` | บอก GitHub Pages ว่าไม่ต้องประมวลผลด้วย Jekyll |

> อยากสลับให้เวอร์ชันแรกเป็นหน้าแรก: copy `index-v1.html` ทับ `index.html` แล้ว commit + push

## เปิดดูในเครื่อง
- ดับเบิลคลิกไฟล์ `.html` เปิดด้วยเบราว์เซอร์ได้เลย หรือ
- รันเซิร์ฟเวอร์ท้องถิ่น: `python -m http.server 8123 --bind 127.0.0.1` แล้วเปิด `http://127.0.0.1:8123/index.html`

## อัปเดตเว็บ
```bash
git add -A
git commit -m "แก้ไขหน้าเว็บ"
git push
```
GitHub Pages จะ rebuild ให้เองภายใน 1–2 นาที

## ตั้งค่า Pages (ทำครั้งเดียว)
**Settings → Pages → Source: Deploy from a branch → Branch: `main` / `/ (root)` → Save**
