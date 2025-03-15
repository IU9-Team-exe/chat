import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
import nltk
nltk.download("stopwords")
from nltk.corpus import stopwords
stop = stopwords.words("english")

# Укажите классы (например, 1 – токсичное, 0 – не токсичное)
class_names = [1, 0]

# Чтение данных и заполнение пропусков
df = pd.read_csv('labeled.csv').fillna(' ')

# Разделение данных на обучающую и тестовую выборки
train, test = train_test_split(df, test_size=0.2, random_state=42)

# Определите семя для воспроизводимости (если требуется)
SEED = 42

pipeline_model = Pipeline(steps=[
    ("features", ColumnTransformer([
        ("comment", CountVectorizer(stop_words=stop), "comment")
    ])),
    ('clf', LogisticRegression(random_state=SEED, solver='lbfgs', class_weight='balanced'))
])

X_train = train['comment']
y_train = train['toxic']

pipeline_model.fit(X_train, y_train)
