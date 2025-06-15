import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# === 1. تحميل داتا AJGT وتحويل التسميات ===
df = pd.read_excel("AJGT.xlsx")

# نحافظ فقط على الصفوف اللي فيها نص وتصنيف
df = df[['Feed', 'Sentiment']]
df = df.dropna(subset=['Feed', 'Sentiment'])

# تحويل التصنيفات من Positive/Negative إلى Non-Violent/Violent
df['Sentiment'] = df['Sentiment'].map({'Negative': 1, 'Positive': 0})
df = df.dropna(subset=['Sentiment'])

# === 2. تجهيز البيانات للتدريب ===
X = df['Feed']
y = df['Sentiment']

# === 3. تحويل النصوص إلى تمثيل رقمي (TF-IDF) ===
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

# === 4. تدريب نموذج SVM ===
model = LinearSVC()
model.fit(X_vec, y)

# === 5. تحميل تعليقات اليوتيوب ===
yt_comments = pd.read_excel("output/فيلم قصير  التنمر- bullying_comments.xlsx")
yt_comments = yt_comments[['comment']].dropna()

# === 6. تحويل تعليقات اليوتيوب إلى نفس التمثيل ===
yt_vec = vectorizer.transform(yt_comments['comment'])

# === 7. تصنيف التعليقات ===
yt_comments['prediction'] = model.predict(yt_vec)
yt_comments['prediction'] = yt_comments['prediction'].map({1: "تنمر", 0: "غير تنمر"})

# === 8. حفظ النتائج في ملف Excel ===
yt_comments.to_excel("output/predictions_ajgt.xlsx", index=False)

print("✅ تم تصنيف تعليقات اليوتيوب باستخدام AJGT وتخزين النتائج في: output/predictions_ajgt.xlsx")
