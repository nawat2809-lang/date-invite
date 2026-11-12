# หน้าเว็บขอจีบ ♡

เว็บ static ล้วน ไฟล์เดียวจบ ไม่ต้อง build ไม่ต้องติดตั้งอะไร — HTML + CSS + JS อยู่ในไฟล์เดียว

## ลิงก์เว็บ
- https://nawat2809-lang.github.io/date-invite/ — หน้าแรก (มินิมอล + สติกเกอร์คุโรมิขยับได้)
- https://nawat2809-lang.github.io/date-invite/index-kuromi-v2.html — ไฟล์เดียวกับหน้าแรก
- https://nawat2809-lang.github.io/date-invite/index-kuromi.html — เวอร์ชันคุโรมิแบบการ์ดม่วง + หิมะ
- https://nawat2809-lang.github.io/date-invite/index-mymelody.html — เวอร์ชันมายเมโรดี้ (ชมพูพาสเทล)
- https://nawat2809-lang.github.io/date-invite/index-v1.html — เวอร์ชันแรก
- https://nawat2809-lang.github.io/date-invite/neon-love-heart.html — หัวใจ neon ที่ประกอบจากคำบอกรักหลายภาษา (canvas)

## ไฟล์ที่มี
| ไฟล์ | คำอธิบาย |
| --- | --- |
| `index.html` | หน้าแรกของเว็บ = เวอร์ชันมินิมอล + สติกเกอร์ขยับ |
| `index-kuromi-v2.html` | ไฟล์เดียวกัน ใช้เป็นลิงก์ตรงได้ |
| `index-kuromi.html` | เวอร์ชันคุโรมิแบบการ์ดม่วง + หิมะตก |
| `index-mymelody.html` | เวอร์ชันมายเมโรดี้ (โทนชมพูพาสเทล) |
| `index-v1.html` | เวอร์ชันแรก |
| `neon-love-heart.html` | หัวใจ neon จากคำบอกรักหลายภาษา วาดด้วย canvas แตะเพื่อเล่นใหม่ |
| `.nojekyll` | บอก GitHub Pages ว่าไม่ต้องประมวลผลด้วย Jekyll |

> อยากสลับหน้าแรก: copy ไฟล์ที่ต้องการทับ `index.html` แล้ว commit + push

## เปิดดูในเครื่อง
- ดับเบิลคลิกไฟล์ `.html` เปิดด้วยเบราว์เซอร์ได้เลย หรือ
- รันเซิร์ฟเวอร์ท้องถิ่น: `python -m http.server 8123 --bind 127.0.0.1` แล้วเปิด `http://127.0.0.1:8123/index.html`

## อัปเดตเว็บ
```bash
git add -A
git commit -m "แก้ไขหน้าเว็บ"
git push
```
GitHub Pages จะ rebuild ให้เองภายใน 1-2 นาที

## ตั้งค่า Pages (ทำครั้งเดียว)
**Settings → Pages → Source: Deploy from a branch → Branch: `main` / `/ (root)` → Save**
