# coding utf-8

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier #GBM algorithm
from sklearn import cross_validation, metrics   #Additional scklearn functions
from sklearn.grid_search import GridSearchCV   #Perforing grid search
from sklearn.datasets import make_hastie_10_2
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor

import matplotlib.pylab as plt



def predict():
    df_Pos = pd.read_csv('shun.csv')
    df_Neg = pd.read_csv('ni.csv')
    X_pos = df_Pos.iloc[:,1:9].as_matrix()
    X_neg = df_Neg.iloc[:,1:9].as_matrix()
    #print(X_pos)

    #for column in df_Pos.columns:
     #   print(column)

    for row in df_Pos.iterrows():
        df_Pos.sort()
        print(len(row))
        break

    '''X_all = np.array([])
    step = 5
    for i in range(len(X_pos)-step):
        X_tmp = np.array([])
        for j in range(i, i+step):
            X_tmp = np.append(X_tmp, X_pos[j])
        X_all = np.append(X_all,X_tmp)
    X_all = np.reshape(X_all, (-1, 8*step))
    y_all = X_pos[5:, 6]

    print(len(X_all))
    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X_all, y_all, test_size=0.2)'''

    '''X_train = X_all[:]
    X_test = X_all[len(X_all) * 3 / 4:]
    y_train = y_all[:len(y_all) * 3 / 4]
    y_test = y_all[len(X_all) * 3 / 4:]'''
    #print(y_train)
    #print(X_train)

    '''
    clf = GradientBoostingRegressor(n_estimators=100, learning_rate=1.0, max_depth=3, random_state=0)
    clf.fit(X_train, y_train)
    y_predict = clf.predict(X_test)
    y_predict = [int(elem) for elem in y_predict]
    T = list(range(len(y_predict)))
    print(len(T))
    print(y_test)
    print(y_predict)
    plt.plot(T, y_predict,label="$predict$",color="red", linewidth=2)
    plt.plot(T, y_test,"b--",label="$real$")
    plt.legend(loc=1)
    plt.xlabel('Date')
    plt.ylabel('Num')
    plt.show()

    mse = mean_squared_error(y_test, clf.predict(X_test))
    print("MSE: %.4f" % mse)'''
    return


if __name__ == '__main__':
    predict()