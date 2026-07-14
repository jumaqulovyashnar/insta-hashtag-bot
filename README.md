# Instagram Hashtag Extractor Bot (Clean Architecture)

Ushbu Telegram bot Instagram postlari va Reels’laridan hashtaglarni ajratib oladi va foydalanuvchidan majburiy kanal obunasini talab qiladi.

Loyiha arxitekturasi **Clean Architecture** qoidalariga moslab qayta yozildi.

## Asosiy O'zgarishlar va Imkoniyatlar:
1. **Kommentariyalarni tekshirish (Fallback)**: Agar post tavsifida (caption) hashtaglar topilmasa, bot avtomatik ravishda postning birinchi top-level kommentariyalaridan hashtaglarni qidiradi (chunki ko'plab mualliflar hashtaglarni birinchi kommentariyada qoldirishadi).
2. **Shaffof javoblar (Transparency)**: Foydalanuvchiga bot qaysi matnni o'qiganini ko'rsatish uchun parsed qilingan matnning dastlabki 200 ta belgisi (tavsif yoki kommentariyadan) preview ko'rinishida yuboriladi.
3. **Unicode Hashtag matching**: Istalgan tildagi (Kirill, Lotin, Arab, Xitoy va h.k.) hashtaglar xatosiz ajratib olinadi.
4. **Singleton Lock (Duplicate Process Prevention)**: Windows tizimida orqa fonda bir nechta bot jarayonlari (`python3.13`) ishlab qolib, o'zaro to'qnashuv (`Conflict`) yuzaga kelishini oldini olish uchun `filelock` asosida ishlaydigan singleton lock o'rnatildi. Ikkinchi marta botni ishga tushirish taqiqlanadi.
5. **Graceful Shutdown**: Bot o'chirilayotganda Telegram polling seansini chiroyli yopadi va lock faylni bo'shatadi.

---

## Arxitektura Strukturasi:
- `domain/` — Soxta arxitektura va pure biznes mantiq (Entity, Value Objects, Pure Services). Hech qanday Django yoki aiogram kutubxonalariga bog'liq emas.
- `application/` — Tizim use case'lari (Extract, Register, Check Subscription) va Gateway/Repository interface’lari (Ports).
- `infrastructure/` — Ma'lumotlar bazasi va tashqi kutubxona adapterlari (yt-dlp, Django ORM, aiogram).
- `presentation/` — Yetkazib berish mexanizmi (Telegram bot handlerlari, main compositions va Django admin).
- `botapp/` — Shunchaki Django persistence model schemalari.

---

## O'rnatish va Ishga tushirish

1. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. Django ma'lumotlar bazasini sozlang va migratsiyalarni yurgizing:
   ```bash
   python manage.py migrate
   ```

3. Botni ishga tushiring:
   ```bash
   python -m presentation.bot.main
   ```

4. Django Admin panelini yoqish (alohida terminalda):
   ```bash
   python manage.py runserver
   ```

---

## Testlarni yurgizish

Tizimdagi barcha unit va integration testlarini yurgizish uchun quyidagi buyruqni bering:
```bash
python -m unittest discover -s tests
```
