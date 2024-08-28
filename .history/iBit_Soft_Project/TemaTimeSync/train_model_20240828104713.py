import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import seaborn as sns
import matplotlib.pyplot as plt


employee_data = pd.read_csv("C:\\Users\\Administrator\\Desktop\\iBit_Soft_Project_-1\\iBit_Soft_Project\\TemaTimeSync\\train.csv")

#no missing values

# Encode categorical features (whether the person is late or not)
label_encoders = {}
for column in data.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    employee_data[column] = le.fit_transform(employees_data[column])
    label_encoders[column] = le


# Feature-target separation
X = employee_data.drop(columns=['IS LATE'])  
y = employee_data['IS LATE']


# Normalize numerical features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

#splitting the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)


#initializing the model(most deal for making the predictions)
model = RandomForestClassifier(n_estimators=100, random_state=42)

#Model training
model.fit(X_train, y_train)

#Model Testing
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy:.2f}')

#Confusion Matrix
matrix = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=model.classes_, yticklabels=model.classes_)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

report = classification_report(y_test, y_pred)
print('The Classification Report:')
print(report)

# Save the model, scaler, and label encoders
joblib.dump(model, 'random_forest_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoders, 'label_encoders.pkl')


