import pandas as pd  
import numpy as np
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import math

verbose = 1
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'

# Setup
def setup_data(depotFile, stopsFile):
    df1 = pd.read_csv(depotFile, low_memory=False)
    df2 = pd.read_csv(stopsFile, low_memory=False)
    df2 = df2[['City','Zip','Lat', 'Long']]
    return df1, df2

# perform  the scraping
def performScraping(zipInfo):
    
    zipInfo['population'] = zipInfo['area'] = None
    
    # Loop through al lthe zips 
    for i in range(0, len(zipInfo)):
        
        Z = zipInfo.Zip[i]
        
        # Get response and content of website 
        url = "https://www.zip-codes.com/zip-code/" + str(Z) + "/zip-code-" + str(Z)
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        page_content = BeautifulSoup(response.data)
        findInfo = page_content.find_all('td', {'class': 'info'})

        if verbose:
            print(str(i) + " -- " + str(url))

        # Safety check
        if len(findInfo) > 0:
            population = findInfo[19]
            area = findInfo[45]

            # Different table position
            if findInfo[19].text.startswith("<"):
                population = findInfo[20]
                area = findInfo[46]
                
            # Insert values into DF
            if population is None:
                zipInfo.iloc[i, 2] = None
            else:
                zipInfo.iloc[i, 2] = population.text
            
            if population is None:
                zipInfo.iloc[i, 3] = None
            else:
                zipInfo.iloc[i, 3] = area.text
    return zipInfo 

# Remove commas and sq-mi. Convert str to float; convert square miles to square km
def cleanVariables(zipInfo):
    zipInfo['population'] = zipInfo['population'].str.replace(',', '')
    zipInfo['area'] = (zipInfo['area'].str.replace('sq mi', ''))
    
    zipInfo.population = zipInfo.population.astype(float)
    zipInfo.area = zipInfo.area.astype(float)
    
    zipInfo['area']=zipInfo['area'].apply(lambda x: x/0.38610)
    zipInfo['density'] = zipInfo['population'] / zipInfo['area']
    
    return zipInfo

def main():
    depot, stops = setup_data(prefix+'depot_geocodes.csv', prefix+'stop_geocodes_fixed.csv')
    zips = stops["Zip"].drop_duplicates().reset_index()
    del zips['index']
    temp = Counter(stops["Zip"])
    
    zipInfo = pd.DataFrame(list(temp.items()), columns = ['Zip','studentCount'])
    zipInfo = performScraping(zipInfo)
    zipInfo = cleanVariables(zipInfo)
    return zipInfo

zipInfo = main()
zipInfo.to_csv('zipInfo.csv', header=True, encoding='utf-8', index=False)

########################################################################
# Normal distribution
zips = zipInfo['studentCount']
avgZips = np.average(zips)
variance = (np.std(zips))**2
mu = avgZips
sigma = math.sqrt(variance)
x = np.linspace(mu - 3*sigma, mu + 3*sigma, 100)
plt.plot(x,mlab.normpdf(x, mu, sigma))
plt.show()

