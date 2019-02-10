import pandas as pd 
import numpy as np 
import pickle


# setupSurvey
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

# format surveys 
def checkSurvey(survey, phoneBook):
    
    for index, row in survey.iterrows():
        
        route = int(row['Route'])
        count = phoneBook[phoneBook.AM_Route == str(route)].count()[0]
        
        if count != 0:
            survey.at[index, 'Assigned_Count'] = count 
        
        if str(survey.at[index, 'Day1']) != str('nan'):
            if survey.at[index, 'Day1'] > survey.at[index, 'Assigned_Count']:
                survey.at[index, 'Day1'] = survey.at[index, 'Assigned_Count']
            
        if str(survey.at[index, 'Day2']) != str('nan'):
            if survey.at[index, 'Day2'] > survey.at[index, 'Assigned_Count']:
                survey.at[index, 'Day2'] = survey.at[index, 'Assigned_Count']
        
        if str(survey.at[index, 'Day3']) != str('nan'):
            if survey.at[index, 'Day3'] > survey.at[index, 'Assigned_Count']:
                survey.at[index, 'Day3'] = survey.at[index, 'Assigned_Count']

    return survey 

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
augSurvey = setupSurvey(prefix+'augSurvey.csv')
septSurvey = setupSurvey(prefix+'septSurvey.csv')
phoneBook = setupPhoneBook(prefix+'totalPhonebook.csv')

new_augSurvey = checkSurvey(augSurvey, phoneBook)
new_septSurvey = checkSurvey(septSurvey, phoneBook)

new_augSurvey.to_csv('new_augSurvey.csv', header=True, encoding='utf-8', index=False)
new_septSurvey.to_csv('new_septSurvey.csv', header=True, encoding='utf-8', index=False)
