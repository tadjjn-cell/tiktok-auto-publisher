# دليل الإعداد — TikTok Auto Publisher

> صافط الفيديو ديالك لـ channel Telegram مخصص (مثلاً "TikTok Queue") مع caption قصيرة، والبوت كيدير الباقي: بحث عن trends، كتابة caption + hashtags بالذكاء الاصطناعي، ونشر الفيديو على TikTok تلقائياً. كلشي **مجاني**، كيخدم على GitHub Actions بلا PC.

---

## ⚠️ فرق مهم مع YouTube: TikTok Audit

TikTok، خلاف Google، كيقيّد الـ Content Posting API:
- **Unaudited app** (قبل ما يوافق عليها TikTok): الفيديوهات كيتنشرو **"SELF_ONLY"** (خاص بيك، ماشي عام) بغض النظر على شنو تحط فـ config.
- بش تنشر **عام** (public)، خاصك تدير "App Review / Audit" فـ TikTok for Developers — هادشي كيتطلب وقت (أيام لـ أسابيع) وكيتطلب تعبئة تفاصيل على التطبيق ديالك.

الخبر الزوين: بحال أنت غير كتنشر لـ compte ديالك (ماشي app عمومي لناس آخرين)، الفيديوهات غادي تولي private فبدايتها، ومنبعد نديرو audit request بش توليو public.

---

## الخطوة 1: TikTok Developer App

1. دخل [developers.tiktok.com](https://developers.tiktok.com) وسجل بحساب TikTok ديالك.
2. **Manage apps** > **Create an app**.
3. عمر التفاصيل (اسم، وصف).
4. من "Add products"، زيد:
   - **Login Kit**
   - **Content Posting API**
5. فـ "Login Kit" settings، خاصك تحط **Redirect URI** — خاصها تكون domain موثّق (verified). نقدرو نستعملو نفس GitHub Pages اللي درنا لـ YouTube project (`https://tadjjn-cell.github.io/...`), وغادي نديرو verification file جديدة.
6. احتافظ بـ **Client Key** و **Client Secret**.

---

## الخطوة 2: دير Telegram Channel مخصص

(دايرها ديجا: "TikTok Queue" channel، private).

```bash
python -m pip install -r setup/requirements.txt
```

نسخ `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` / `TELEGRAM_SESSION` من `.env` ديال YouTube project لـ `.env` ديال هاد المشروع (نفس compte Telegram، ما خاصكش تعاود login).

من بعد:

```bash
python setup/list_telegram_chats.py
```

غادي يطبع ليك لائحة ديال الـ chats/channels ديالك مع الـ id ديالهم. قلب على "TikTok Queue" وانسخ الـ id (رقم، ممكن يكون سالب مثلا `-1001234567890`) وحطو فـ `TELEGRAM_SOURCE_CHAT` فـ `.env`.

---

## الخطوة 3: جيب TikTok Access/Refresh Token

```bash
python setup/get_tiktok_token.py
```

غادي يطلب منك client_key, client_secret, و redirect_uri (نفس اللي حطيتي فـ TikTok app). غادي يطبع ليك رابط — حل فـ browser، دخل بـ TikTok، عطي الصلاحية. من بعد كيوجّهك لصفحة (redirect) — نسخ الرابط الكامل من شريط العنوان ولصقه فـ terminal.

غادي يطبع ليك:
```
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_ACCESS_TOKEN=...
TIKTOK_REFRESH_TOKEN=...
```

---

## الخطوة 4: GitHub Repo + Secrets

نفس الخطوات ديال YouTube project:

1. `git init && git add . && git commit -m "Initial commit"`
2. دير repo جديد فـ GitHub، ربطو (`git remote add origin ...`), push
3. **Settings > Actions > General > Workflow permissions** → "Read and write permissions" → Save
4. **Settings > Secrets and variables > Actions** → زيد:

| Secret |
|---|
| `GROQ_API_KEY` |
| `TELEGRAM_API_ID` |
| `TELEGRAM_API_HASH` |
| `TELEGRAM_SESSION` |
| `TELEGRAM_SOURCE_CHAT` |
| `TIKTOK_CLIENT_KEY` |
| `TIKTOK_CLIENT_SECRET` |
| `TIKTOK_ACCESS_TOKEN` |
| `TIKTOK_REFRESH_TOKEN` |

---

## الخطوة 5: جرب

**Actions** tab > **TikTok Auto Publisher** > **Run workflow**.

صيفط فيديو (vertical, قصير) + caption قصيرة لـ "TikTok Queue" channel، شغل الـ workflow يدوياً.

الفيديو غادي يبان فـ TikTok ديالك تحت **"Only me" / Drafts** (privacy_level مقيّدة حتى يوافق TikTok على الـ app).

---

## الخطوة 6 (بعدين): طلب Audit بش تنشر Public

مجرد ما تأكد بلي كلشي خدام (فيديوهات كيتنشرو private بنجاح)، دير من TikTok Developer Portal:
- **App Review** / **Submit for audit** فـ الـ Content Posting API product
- عبي المعلومات المطلوبة (استعمال شخصي، demo video إلخ)
- استنى موافقة TikTok (أيام لـ أسابيع)

من بعد الموافقة، بدّل `privacy_level` فـ `config.yaml` لـ `"PUBLIC_TO_EVERYONE"`.
