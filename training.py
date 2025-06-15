import pandas as pd
import nltk
import re
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

# تحميل بيانات NLTK المطلوبة
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

class ArabicViolenceClassifier:
    def __init__(self):
        self.pipeline = None

    def preprocess_arabic_text(self, text):
        if pd.isna(text):
            return ""
        text = str(text)
        text = re.sub(r'[a-zA-Z0-9]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
        return text.strip()

    def load_dataset(self, file_path):
        try:
            df = pd.read_excel(file_path)
            if 'comment' not in df.columns or 'label' not in df.columns:
                print("الملف يجب أن يحتوي على أعمدة: comment و label")
                return None, None
            df['processed_text'] = df['comment'].apply(self.preprocess_arabic_text)
            df = df[df['processed_text'].str.len() > 0]
            return df['processed_text'].tolist(), df['label'].tolist()
        except Exception as e:
            print(f"خطأ في تحميل الملف: {e}")
            return None, None

    def train_model(self, texts, labels, model_type='svm'):
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        if model_type == 'nb':
            classifier = MultinomialNB()
        elif model_type == 'svm':
            classifier = SVC(kernel='linear', probability=True)
        else:
            classifier = MultinomialNB()

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ('clf', classifier)
        ])

        print(f"Training model: {model_type}")
        self.pipeline.fit(X_train, y_train)
        y_pred = self.pipeline.predict(X_test)
        print(f"\n✅ Accuracy: {accuracy_score(y_test, y_pred):.2f}")
        print("\n📊 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Non-Bullying', 'Bullying']))

    def predict_text(self, text):
        processed = self.preprocess_arabic_text(text)
        pred = self.pipeline.predict([processed])[0]
        prob = self.pipeline.predict_proba([processed])[0]
        return {
            "prediction": "Bullying" if pred == 1 else "Non-Bullying",
            "confidence": max(prob)
        }

def main():
    classifier = ArabicViolenceClassifier()
    print("=== Arabic Violence Detection System ===")
    print("1. تحميل البيانات وتدريب النموذج...")
    texts, labels = classifier.load_dataset("fake_comments_dataset.xlsx")

    if texts is None or labels is None:
        print("❌ فشل في تحميل البيانات. تأكد من الملف.")
        return

    classifier.train_model(texts, labels, model_type='svm')

    while True:
        user_input = input("\n📝 أدخل تعليق للتجربة (أو 'quit' للخروج): ").strip()
        if user_input.lower() == 'quit':
            break
        result = classifier.predict_text(user_input)
        print(f"🔎 التصنيف: {result['prediction']}, الثقة: {result['confidence']:.2f}")

if __name__ == "__main__":
    main()
