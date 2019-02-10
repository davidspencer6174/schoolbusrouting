import pandas as pd 
import numpy as np 
from scipy.optimize import minimize
from scipy.stats import norm
import matplotlib.pyplot as plt
from math import log
import operator
import collections

verbose = 1

############################
# SETUP 
############################

# setup survey
def setupSurvey(file):
    df = pd.read_csv(file, low_memory=False, keep_default_na=True)
    df = df[['Route','Day1', 'Day2','Day3','Aides',
             'Assigned_Count']]
    return df

# setupPhonebook
def setupPhoneBook(file):
    df = pd.read_csv(file, dtype={"Zip": float, "AM_Route": str}, low_memory=False)
    df = df[['Zip', 'AM_Route']]
    df = df[df['AM_Route'] != str(9500)]
    df = df.sort_values(by=['Zip', 'AM_Route'])
    df = df.dropna()
    return df.astype(str)    

# Obtain the rz pairs
def getRouteZipPairs(phoneBook, survey): 
    
    df = pd.DataFrame()
    df["routes"] = np.sort(phoneBook.AM_Route.unique())
    df['zipCode'] = [np.sort(phoneBook.Zip.unique().tolist())] * len(df)
    df['studentCount'] = None

    for index, row in df.iterrows():
        
        route = row["routes"]
        studentCount = []
        
        for zipcode in row["zipCode"]:
            
            count = phoneBook[(phoneBook.AM_Route == str(route)) 
            & (phoneBook.Zip == zipcode)][['AM_Route','Zip']].count()[0]
            
            studentCount.append(count)

            if verbose:
                print("Route: " + str(route) + " -- Zipcode: " 
                      + str(zipcode) + " -- Count: " + str(count))
            
        df.at[index, 'studentCount'] = studentCount
    return df 

# Obtain the zr pairs
def getZipRoutePairs(phoneBook, survey): 
    
    df = pd.DataFrame()
    df["zipCode"] = np.sort(phoneBook.Zip.unique())
    df['routes'] = [survey['Route'].values.tolist()]*len(df)
    df['studentCount'] = None

    for index, row in df.iterrows():
        
        zipcode = row["zipCode"]
        studentCount = []
        
        for route in row["routes"]:
            
            count = phoneBook[(phoneBook.AM_Route == str(route)) 
            & (phoneBook.Zip == zipcode)][['AM_Route','Zip']].count()[0]
            
            studentCount.append(count)

            if verbose:
                print("Zipcode: " + str(zipcode) + " -- Route: " 
                      + str(route) + " -- Count: " + str(count))
            
        df.at[index, 'studentCount'] = studentCount
    return df 

# update phonebook
def updatePhoneBook(phoneBook, augSurvey, septSurvey):
    
    phoneBook['days'] = [list() for x in range(len(phoneBook.index))]
    phoneBook['Assigned1'] = phoneBook['Assigned2'] = 0
    
    for index, row in phoneBook.iterrows():
        route = row['AM_Route']
            
        augTemp = (augSurvey.loc[augSurvey['Route'] == int(route)]) 
        septTemp = (septSurvey.loc[septSurvey['Route'] == int(route)]) 
                
        if not augTemp.empty:
            phoneBook.at[index, 'days'].extend(list(map(float, list(augTemp.loc[:,'Day1':'Day3'].values[0]))))
            phoneBook.at[index, 'Assigned1'] = float(augTemp.Assigned_Count)

        if not septTemp.empty:
            phoneBook.at[index, 'days'].extend(list(map(float, list(septTemp.loc[:,'Day1':'Day3'].values[0]))))
            phoneBook.at[index, 'Assigned2'] = float(septTemp.Assigned_Count)
            
        if augTemp.empty and septTemp.empty:
            phoneBook = phoneBook.drop(index)
            
    phoneBook["Assigned"]= phoneBook[["Assigned1", "Assigned2"]].max(axis=1)
    phoneBook = phoneBook.drop(['Assigned2','Assigned1'], axis=1)

    return phoneBook

# I propose to estimate pz by maximizing log-likelihood of the sri values. 
def getLogs(phoneBook):
    
    phoneBook['prob'] = None
    
    for index, row in phoneBook.iterrows():
        days1 = row['days']
        assign1 = row['Assigned']
        
        probs = []
        logs = []
        prob = 0.001
        
        while prob<=1:
            L = (np.nansum(days1) * log(prob)) + (np.nansum(assign1-np.array(days1)) * log(1-prob))
            prob += 0.001
            
            logs.append(L)
            probs.append(prob)            
    
        index2, value = max(enumerate(logs), key=operator.itemgetter(1))
        phoneBook.at[index, 'prob']=probs[index2]
        
    return phoneBook
    
############################
# Implementation of steps written out 
# Inserting student count (list) and probs (list) will give us a mu and sigma
############################

def computeStats(studentCount, probs):
    
    mu = sum(np.multiply(studentCount,probs))
    sig = sum(list(map(lambda x, y: x*y*(1-y), studentCount, probs)))       
    
    z_1 = (S_r - 0.5 - mu)/(sig**2) 
    z_2 = (S_r + 0.5 - mu)/(sig**2) 
    prob = norm.cdf(z_2) - norm.cdf(z_1) 

    return prob

# overall log likelihood is the sum of the probabilities 
def overallLogLike(probs):
    LL = np.sum(log(probs))
    return LL 

res = minimize(computeStats, method='BFGS', options={'disp': False})
    
############################
# Commands 
############################

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
phoneBook = setupPhoneBook(prefix+'totalPhonebook.csv')
augSurvey = setupSurvey(prefix+'augSurvey.csv')
septSurvey = setupSurvey(prefix+'septSurvey.csv')

# Get PAIRS 
# zipRoutePairs = getZipRoutePairs(phoneBook, augSurvey)
# routeZipPairs = getRouteZipPairs(phoneBook, augSurvey)
# zipRoutePairs = estimateProb(zipRoutePairs)

# update PhoneBook
newPhoneBook = phoneBook.drop_duplicates(['Zip','AM_Route'],keep= 'last')
newPhoneBook = updatePhoneBook(newPhoneBook, augSurvey, septSurvey)
newPhoneBook = getLogs(newPhoneBook)

# logLikelihood of PZs 
newPB = pd.DataFrame({'zips':phoneBook['Zip'].drop_duplicates()})
newPB['probs'] = 0.5

### Pickling Commands 
zipRoutePairs.to_pickle('zipRoutePairs.p')
routeZipPairs.to_pickle('routeZipPairs.p')
newPhoneBook.to_pickle('newPhoneBook.p')

### UNPickling Commands 
routeZipPairs = pd.read_pickle(prefix+"routeZipPairs.p")
zipRoutePairs = pd.read_pickle(prefix+"zipRoutePairs.p")
newPhoneBook = pd.read_pickle(prefix+"newPhoneBook.p")


