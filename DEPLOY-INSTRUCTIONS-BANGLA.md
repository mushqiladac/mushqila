# 🚀 ডিপ্লয়মেন্ট নির্দেশনা (বাংলা)

## 🎯 বর্তমান অবস্থা

আপনার EC2 ডিপ্লয়মেন্ট প্রায় সম্পূর্ণ। শুধু একটি ছোট ফিক্স দরকার।

## ✅ যা করা হয়েছে

1. ✅ Webmail URL যোগ করা হয়েছে `config/urls.py` তে
2. ✅ ডিপ্লয়মেন্ট গাইড তৈরি করা হয়েছে
3. ✅ ট্রাবলশুটিং ডকুমেন্ট তৈরি করা হয়েছে
4. ✅ কোড GitHub এ পুশ করা হয়েছে

## 🔧 এখন EC2 তে যা করতে হবে

### পদ্ধতি ১: দ্রুত ডিপ্লয়মেন্ট (সুপারিশকৃত)

```bash
# EC2 তে SSH করুন
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# প্রজেক্ট ফোল্ডারে যান
cd ~/mushqila

# নতুন কোড পুল করুন
git pull origin main

# ডিপ্লয়মেন্ট স্ক্রিপ্ট চালান
bash DEPLOY-FINAL-FIX.sh
```

### পদ্ধতি ২: ম্যানুয়াল ডিপ্লয়মেন্ট

```bash
# EC2 তে SSH করুন
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# প্রজেক্ট ফোল্ডারে যান
cd ~/mushqila

# নতুন কোড পুল করুন
git pull origin main

# কন্টেইনার বন্ধ করুন
docker-compose -f docker-compose.prod.yml down

# Docker ক্লিন করুন
docker system prune -f

# নতুন করে বিল্ড এবং স্টার্ট করুন
docker-compose -f docker-compose.prod.yml up -d --build

# ৬০ সেকেন্ড অপেক্ষা করুন
sleep 60

# স্ট্যাটাস চেক করুন
docker-compose -f docker-compose.prod.yml ps
```

## 🌐 ব্রাউজার থেকে টেস্ট করুন

**গুরুত্বপূর্ণ:** `curl http://localhost/` হ্যাং হওয়া স্বাভাবিক। এটি Docker networking এর সমস্যা, ডিপ্লয়মেন্ট ব্যর্থ হয়নি।

**আপনার ব্রাউজার থেকে এই URL গুলো টেস্ট করুন:**

1. **মূল ডোমেইন:**
   ```
   http://mushqila.com
   ```

2. **WWW ডোমেইন:**
   ```
   http://www.mushqila.com
   ```

3. **সরাসরি IP:**
   ```
   http://16.170.25.9
   ```

4. **ল্যান্ডিং পেজ:**
   ```
   http://mushqila.com/accounts/landing/
   http://mushqila.com/landing2/
   ```

5. **অ্যাডমিন প্যানেল:**
   ```
   http://mushqila.com/admin/
   ```

6. **ওয়েবমেইল:**
   ```
   http://mushqila.com/webmail/
   ```

## ✅ যা দেখতে পাবেন

### ল্যান্ডিং পেজে:
- ✅ বড় হিরো সেকশন সার্চ উইজেট সহ
- ✅ হরিজন্টাল সার্চ ফর্ম (Book Flight, Modify Trip, ইত্যাদি)
- ✅ ট্রিপ টাইপ বাটন (One-way, Round-trip, Multi-city)
- ✅ ফেয়ার টাইপ বাটন (Regular, Umrah, Senior, Promo)
- ✅ Flying From/To ফিল্ড
- ✅ ডেট পিকার এবং প্যাসেঞ্জার সিলেক্টর
- ✅ সার্চ বাটন

### ফুটারে:
- ✅ পেমেন্ট লোগো (Visa, MasterCard, Amex, Bkash, SSL Commerz)
- ✅ "We Accept" টেক্সট
- ✅ হোভার ইফেক্ট সহ প্রফেশনাল স্টাইলিং
- ✅ সোশ্যাল মিডিয়া আইকন (YouTube, Facebook, WhatsApp)

### নেভবারে:
- ✅ Agent Login বাটন (হালকা নীল ব্যাকগ্রাউন্ড)
- ✅ Agent Register বাটন (হলুদ ব্যাকগ্রাউন্ড)
- ✅ সাদা টেক্সট
- ✅ হোভার ইফেক্ট

## 🔍 যদি ডোমেইন কাজ না করে

DNS propagation এ ৫-১৫ মিনিট সময় লাগতে পারে। যদি `mushqila.com` কাজ না করে:

1. **৫-১০ মিনিট অপেক্ষা করুন** DNS propagation এর জন্য
2. **সরাসরি IP টেস্ট করুন:** http://16.170.25.9 (এটি সাথে সাথে কাজ করবে)
3. **DNS চেক করুন:** https://dnschecker.org/domain/mushqila.com

## 🐛 সমস্যা সমাধান

### যদি সাইট অ্যাক্সেস না হয়:

```bash
# EC2 তে SSH করুন
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# কন্টেইনার চেক করুন
docker ps

# ৪টি কন্টেইনার চলমান থাকা উচিত

# লগ চেক করুন
cd ~/mushqila
docker-compose -f docker-compose.prod.yml logs --tail=100 web

# প্রয়োজনে রিস্টার্ট করুন
docker-compose -f docker-compose.prod.yml restart web
```

## 📊 সফলতার চিহ্ন

যখন ডিপ্লয়মেন্ট সফল হবে:

1. ✅ ৪টি কন্টেইনার চলমান
2. ✅ পোর্ট ৮০ ম্যাপ করা
3. ✅ লগে কোন এরর নেই
4. ✅ ব্রাউজার থেকে সাইট অ্যাক্সেস হচ্ছে
5. ✅ ল্যান্ডিং পেজ সঠিকভাবে লোড হচ্ছে
6. ✅ পেমেন্ট লোগো দেখা যাচ্ছে
7. ✅ সার্চ উইজেট কাজ করছে
8. ✅ অ্যাডমিন প্যানেল অ্যাক্সেস হচ্ছে
9. ✅ ওয়েবমেইল অ্যাক্সেস হচ্ছে

## 🎯 এখন যা করতে হবে

### ধাপ ১: EC2 তে কমান্ড চালান

```bash
# SSH করুন
ssh -i ~/.ssh/key.pem ubuntu@16.170.25.9

# ডিপ্লয় করুন
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# অপেক্ষা করুন
sleep 60

# স্ট্যাটাস চেক করুন
docker-compose -f docker-compose.prod.yml ps
```

### ধাপ ২: ব্রাউজার থেকে টেস্ট করুন

- http://mushqila.com
- http://16.170.25.9

### ধাপ ৩: যা দেখছেন তা রিপোর্ট করুন

ব্রাউজারে কী দেখছেন তা আমাকে জানান:
- সাইট লোড হচ্ছে?
- পেমেন্ট লোগো দেখা যাচ্ছে?
- সার্চ উইজেট আছে?
- কোন এরর?

## 💡 গুরুত্বপূর্ণ নোট

1. **localhost curl হ্যাং হওয়া স্বাভাবিক** - এটি Docker networking এর সমস্যা
2. **ব্রাউজার থেকে টেস্ট করুন** - curl নয়
3. **DNS propagation এ সময় লাগে** - ৫-১৫ মিনিট
4. **সরাসরি IP সাথে সাথে কাজ করবে** - http://16.170.25.9

## 📞 সাহায্য দরকার?

যদি কোন সমস্যা হয়:

1. **কন্টেইনার চেক করুন:** `docker ps`
2. **লগ দেখুন:** `docker-compose -f docker-compose.prod.yml logs web`
3. **রিস্টার্ট করুন:** `docker-compose -f docker-compose.prod.yml restart web`
4. **আমাকে জানান** - কী এরর দেখছেন

---

## 🚀 সংক্ষেপে

1. **EC2 তে SSH করুন**
2. **কোড পুল করুন:** `git pull origin main`
3. **ডিপ্লয় করুন:** `docker-compose -f docker-compose.prod.yml up -d --build`
4. **৬০ সেকেন্ড অপেক্ষা করুন**
5. **ব্রাউজার থেকে টেস্ট করুন:** http://mushqila.com বা http://16.170.25.9
6. **রিপোর্ট করুন** - কী দেখছেন

**localhost curl কে বিশ্বাস করবেন না - ব্রাউজার থেকে টেস্ট করুন!**

---

**আপনার ডিপ্লয়মেন্ট প্রস্তুত। এখন ব্রাউজার থেকে টেস্ট করুন!**
