# data analysis and wrangling
import pandas as pd
import numpy as np
import random as rnd

# visualization
import seaborn as sns
import matplotlib.pyplot as plt

# machine learning
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import Perceptron
from sklearn.linear_model import SGDClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn import preprocessing

training_data = pd.read_csv('train.csv')
test_data = pd.read_csv('test.csv')


## Set of functions to transform features into more convenient format.
#
# Code performs three separate tasks:
#   (1). Pull out the first letter of the cabin feature.
#          Code taken from: https://www.kaggle.com/jeffd23/titanic/scikit-learn-ml-from-start-to-finish
#   (2). Add column which is binary variable that pertains
#        to whether the cabin feature is known or not.
#        (This may be relevant for Pclass = 1).
#   (3). Recasts cabin feature as number.
def simplify_cabins(data):
    data.Cabin = data.Cabin.fillna('N')
    data.Cabin = data.Cabin.apply(lambda x: x[0])

    cabin_mapping = {'N': 0, 'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1,
                     'F': 1, 'G': 1, 'T': 1}
    data['Cabin_Known'] = data.Cabin.map(cabin_mapping)

    le = preprocessing.LabelEncoder().fit(data.Cabin)
    data.Cabin = le.transform(data.Cabin)

    return data


# Recast sex as numerical feature.
def simplify_sex(data):
    sex_mapping = {'male': 0, 'female': 1}
    data.Sex = data.Sex.map(sex_mapping).astype(int)

    return data


# Recast port of departure as numerical feature.
def simplify_embark(data):
    # Two missing values, assign the most common port of departure.
    data.Embarked = data.Embarked.fillna('S')

    le = preprocessing.LabelEncoder().fit(data.Embarked)
    data.Embarked = le.transform(data.Embarked)

    return data


# Extract title from names, then assign to one of five ordinal classes.
# Function based on code from: https://www.kaggle.com/startupsci/titanic/titanic-data-science-solutions
def add_title(data):
    data['Title'] = data.Name.str.extract(' ([A-Za-z]+)\.', expand=False)
    data.Title = data.Title.replace(['Lady', 'Countess', 'Capt', 'Col', 'Don', 'Dr', 'Major',
                                     'Rev', 'Sir', 'Jonkheer', 'Dona'], 'Rare')
    data.Title = data.Title.replace('Mlle', 'Miss')
    data.Title = data.Title.replace('Ms', 'Miss')
    data.Title = data.Title.replace('Mme', 'Mrs')

    # Map from strings to ordinal variables.
    title_mapping = {"Mr": 1, "Miss": 2, "Mrs": 3, "Master": 4, "Rare": 5}

    data.Title = data.Title.map(title_mapping)
    data.Title = data.Title.fillna(0)

    return data


# Drop all unwanted features (name, ticket).
def drop_features(data):
    return data.drop(['Name', 'Ticket'], axis=1)


# Perform all feature transformations.
def transform_all(data):
    data = simplify_cabins(data)
    data = simplify_sex(data)
    data = simplify_embark(data)
    data = add_title(data)
    data = drop_features(data)

    return data


training_data = transform_all(training_data)
test_data = transform_all(test_data)
# Impute single missing 'Fare' value with median
training_data['Fare'] = training_data['Fare'].fillna(training_data['Fare'].median())
test_data['Fare'] = test_data['Fare'].fillna(test_data['Fare'].median())

# Add Age_Known variable
training_data['Age_Known'] = 1
test_data['Age_Known'] = 1
select_null = pd.isnull(training_data['Age'])
training_data.loc[select_null,'Age_Known'] = 0
select_null = pd.isnull(test_data['Age'])
test_data.loc[select_null,'Age_Known'] = 0


all_data = [training_data, test_data]
combined = pd.concat(all_data, ignore_index=True)


# age imputation
train_not = training_data[pd.notnull(training_data['Age'])]
test_not = test_data[pd.notnull(test_data['Age'])]
train_null = training_data[pd.isnull(training_data['Age'])].drop('Age',axis=1)
test_null = test_data[pd.isnull(test_data['Age'])].drop('Age',axis=1)

# Drop 'Survived' as it is the target variable
droplist = 'Survived'.split()
train_not = train_not.drop(droplist, axis=1)
train_null = train_null.drop(droplist, axis=1)

# define training sets
age_train_x = train_not.drop('Age', axis=1)
age_train_y = train_not['Age']

# SVR
svr_rbf = SVR(kernel='rbf', C=1e2, gamma=0.01)
train_null['Age'] = svr_rbf.fit(age_train_x, age_train_y).predict(train_null).round()
test_null['Age'] = svr_rbf.fit(test_not.drop('Age', axis=1), test_not['Age']).predict(test_null).round()

# replace null values in original data frame
training_data.update(train_null)
test_data.update(test_null)

# define regression data sets
X_train = training_data.drop('Survived', axis=1)
Y_train = training_data['Survived']
X_test = test_data.copy()

# Logistic Regression
logreg = LogisticRegression()
logreg.fit(X_train, Y_train)
Y_pred = logreg.predict(X_test)
acc_log = round(logreg.score(X_train, Y_train) * 100, 2)

# Support Vector Machines
svc = SVC()
svc.fit(X_train, Y_train)
Y_pred = svc.predict(X_test)
acc_svc = round(svc.score(X_train, Y_train) * 100, 2)

# k-Nearest Neighbors
knn = KNeighborsClassifier(n_neighbors = 3)
knn.fit(X_train, Y_train)
Y_pred = knn.predict(X_test)
acc_knn = round(knn.score(X_train, Y_train) * 100, 2)

# Gaussian Naive Bayes
gaussian = GaussianNB()
gaussian.fit(X_train, Y_train)
Y_pred = gaussian.predict(X_test)
acc_gaussian = round(gaussian.score(X_train, Y_train) * 100, 2)

# Perceptron
perceptron = Perceptron()
perceptron.fit(X_train, Y_train)
Y_pred = perceptron.predict(X_test)
acc_perceptron = round(perceptron.score(X_train, Y_train) * 100, 2)

# Linear SVC
linear_svc = LinearSVC()
linear_svc.fit(X_train, Y_train)
Y_pred = linear_svc.predict(X_test)
acc_linear_svc = round(linear_svc.score(X_train, Y_train) * 100, 2)

# Stochastic Gradient Descent
sgd = SGDClassifier()
sgd.fit(X_train, Y_train)
Y_pred = sgd.predict(X_test)
acc_sgd = round(sgd.score(X_train, Y_train) * 100, 2)

# Decision Tree
decision_tree = DecisionTreeClassifier()
decision_tree.fit(X_train, Y_train)
Y_pred = decision_tree.predict(X_test)
acc_decision_tree = round(decision_tree.score(X_train, Y_train) * 100, 2)

# Random Forest
random_forest = RandomForestClassifier(n_estimators=13)
random_forest.fit(X_train, Y_train)
Y_pred = random_forest.predict(X_test)
before = Y_pred
random_forest.score(X_train, Y_train)
acc_random_forest = round(random_forest.score(X_train, Y_train) * 100, 2)
print("--Before--")
print(acc_random_forest)

models = pd.DataFrame({
    'Model': ['Support Vector Machines', 'KNN', 'Logistic Regression',
              'Random Forest', 'Naive Bayes', 'Perceptron',
              'Stochastic Gradient Decent', 'Linear SVC',
              'Decision Tree'],
    'Score': [acc_svc, acc_knn, acc_log,
              acc_random_forest, acc_gaussian, acc_perceptron,
              acc_sgd, acc_linear_svc, acc_decision_tree]})
#print(models.sort_values(by='Score', ascending=False))

# use SVM as a new training data point to feed an random forest with reduced estimators
X_train['svc'] = logreg.predict(X_train)
X_test['svc'] = logreg.predict(X_test)

# Random Forest
random_forest = RandomForestClassifier(n_estimators=13)
random_forest.fit(X_train, Y_train)
Y_pred = random_forest.predict(X_test)
print("The number of changed predictions: %d" %np.sum(np.abs(Y_pred - before)))
random_forest.score(X_train, Y_train)
acc_random_forest = round(random_forest.score(X_train, Y_train) * 100, 2)
print("--After--")
print(acc_random_forest)
print(Y_pred)
# submission file
# submission = pd.DataFrame({
#         "PassengerId": test_data['PassengerId'].astype(int),
#         "Survived": Y_pred
#     })
#
# submission.to_csv('../submission.csv', index=False)