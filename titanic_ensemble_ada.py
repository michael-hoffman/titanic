# data analysis and wrangling
import pandas as pd
import numpy as np

# visualization
import matplotlib.pyplot as plt

# machine learning
from sklearn.svm import SVR
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import zero_one_loss
from sklearn.ensemble import AdaBoostClassifier

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

droplist = 'Survived PassengerId Age_Known'.split()
data = training_data.drop(droplist, axis=1)
# ensmeble training and test set
X, y = data, training_data['Survived']
offset = int(data.shape[0] * 0.9)
X_train, y_train = X[:offset], y[:offset]
X_test, y_test = X[offset:], y[offset:]

n_estimators = 400
learning_rate = 0.25

dt_stump = DecisionTreeClassifier(max_depth=1, min_samples_leaf=1)
dt_stump.fit(X_train, y_train)
dt_stump_err = 1.0 - dt_stump.score(X_test, y_test)

ada_real = AdaBoostClassifier(
    base_estimator=dt_stump,
    learning_rate=learning_rate,
    n_estimators=n_estimators,
    algorithm="SAMME.R")
ada_real.fit(X_train, y_train)


# predict survival status
Y_pred = ada_real.predict(test_data.drop(droplist[1:], axis=1))
print(Y_pred)

# fig = plt.figure()
# ax = fig.add_subplot(111)
# ada_real_err = np.zeros((n_estimators,))
# for i, y_pred in enumerate(ada_real.staged_predict(X_test)):
#     ada_real_err[i] = zero_one_loss(y_pred, y_test)
#
# ada_real_err_train = np.zeros((n_estimators,))
# for i, y_pred in enumerate(ada_real.staged_predict(X_train)):
#     ada_real_err_train[i] = zero_one_loss(y_pred, y_train)
#
# ax.plot(np.arange(n_estimators) + 1, ada_real_err,
#         label='Real AdaBoost Test Error',
#         color='orange')
# ax.plot(np.arange(n_estimators) + 1, ada_real_err_train,
#         label='Real AdaBoost Train Error',
#         color='green')
#
# ax.set_ylim((0.0, 0.5))
# ax.set_xlabel('n_estimators')
# ax.set_ylabel('error rate')
#
# leg = ax.legend(loc='upper right', fancybox=True)
# leg.get_frame().set_alpha(0.7)

plt.show()
# submission file
# submission = pd.DataFrame({
#         "PassengerId": test_data['PassengerId'].astype(int),
#         "Survived": Y_pred
#     })
#
# submission.to_csv('../submission.csv', index=False)