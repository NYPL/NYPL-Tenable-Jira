import requests #Calling Tenable API
from contextlib import closing #Dependency of Tenable API
import sqlite3 #SQLite DB
import datetime #Date Formatting
import codecs # Dependency
import time # Sleep
import csv # Making CSV
from src.config import Config


configInformation = Config()



scanNameList = configInformation.getTenableScanName()
accessKey = configInformation.getTenableAccessKey()
secretKey =configInformation.getTenableSecretKey()

for scanName in scanNameList:
    print("\nCurrent Scan:",scanName)

    sqlScanName = scanName.replace("-", "_")

    ### List Scans API - Acquire schedule_uuid
    url = "https://cloud.tenable.com/scans"
    headers = {
        'accept': "application/json",
        'x-apikeys': "accessKey=" + accessKey + ";" + "secretKey=" + secretKey
    }
    response = requests.get(url, headers=headers)
    jsonData = response.json()
    scanList = jsonData["scans"]
    schedule_uuid = ""
    for dictScans in scanList:
        if dictScans["name"] == scanName:
            schedule_uuid = dictScans["schedule_uuid"]
            break
    if schedule_uuid == "":
        print("Error: Cannot find",scanName)
        continue
    ###
    ## Get Scan Details API - Acquire history_id
    url = "https://cloud.tenable.com/scans/" + schedule_uuid
    headers = {
        'accept': "application/json",
        'x-apikeys': "accessKey=" + accessKey + ";" + "secretKey=" + secretKey
    }
    response = requests.request("GET", url, headers=headers)
    jsonData = response.json()
    historyList = jsonData["history"]
    response = requests.request("GET", url, headers=headers)
    jsonData = response.json()

    historyRow = historyList[0] #only need latest row
    sqlHistory = []
    status = 0 #Assume hash map failed
    history_id = historyRow["history_id"]
    creation_date = historyRow["creation_date"]
    creation_date = datetime.datetime.fromtimestamp(creation_date).strftime('%Y-%m-%d')
    #First check if data has been successfully inputted before (avoids repeats)
    connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM "+sqlScanName+"_HISTORY ORDER BY Scan_Date DESC")
    for rowHistory in cursor.fetchall():
        if rowHistory[0] == creation_date:
            if rowHistory[1] == 1:
                print("Data already exists for",creation_date," --> Skipping...")
                status = 1
                break
    if status == 1:
        continue
    elif status == 0:
        print("Data upload has failed in the past or doesn't exist for",creation_date,"re-initializing....")
        cursor.execute("DELETE FROM "+sqlScanName+"_MAP WHERE [Scan_Date] =?",(creation_date,))
        connection.commit()
        sqlHistory = [creation_date,status]
    connection.close()


    ## Export Scan API - Acquire file_id
    url = "https://cloud.tenable.com/scans/" + schedule_uuid + "/export"

    querystring = {"history_id": history_id}

    payload = "{\"format\":\"csv\",\"chapters\":\"Host, Name, Risk,Vulnerability;Priority;Rating;(VPR)\"}" #doesn't do anything...
    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'x-apikeys': "accessKey=" + accessKey + ";" + "secretKey=" + secretKey
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    jsonData = response.json()
    try:
        file_id = jsonData["file"]
    except Exception as e:
        connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
        cursor = connection.cursor()
        if e == 'file':
            print("Error: Scan is currently in progress. Cannot create tickets.")
        else:
            print("Error:",e)
        print("Failed to upload all data for:", creation_date)
        # Current sqlHistory: [creation_date,status]
        sqlHistory.append(0)  # append ticket_status - should be zero
        # sqlHistory.append(status) #append creation_date for scan_status =, in the query
        sqlHistory = tuple(sqlHistory)
        cursor.execute("DELETE FROM " + sqlScanName + "_HISTORY WHERE [Scan_Date] =?", (creation_date,))
        cursor.execute("INSERT INTO " + sqlScanName + "_HISTORY (Scan_Date,Scan_Status,Tickets_Created) VALUES(?,?,?)",
                       sqlHistory)
        connection.commit()
        connection.close()
        continue
    # print(file_id)
    ##

    ## Check Scan Export Status API -- gatekeeper
    url = "https://cloud.tenable.com/scans/"+ schedule_uuid +"/export/"+file_id+"/status"

    headers = {
        'accept': "application/json",
        'x-apikeys': "accessKey=" + accessKey + ";" + "secretKey=" + secretKey
    }

    print()
    print("Checking Scan Status...")
    ready = False
    while ready == False:
        response = requests.request("GET", url, headers=headers)
        jsonData = response.json()
        if jsonData['status'] == "ready":
            print("File ready! Checking contents...")
            ready = True
            time.sleep(2)
        else:
            print("File not ready yet! Waiting 30 seconds")
            time.sleep(30)
    ##

    ## Download Exported Scan API - Acquire csv file
    url = "https://cloud.tenable.com/scans/" + schedule_uuid + "/export/" + file_id + "/download"
    print()
    print("Data for scan:", scanName)
    print("schedule_uuid:", schedule_uuid)
    print("history_id:", history_id)
    print("file_id:", file_id)
    print("Date Scan Created:", creation_date)
    headers = {
        'accept': "application/octet-stream",
        'x-apikeys': "accessKey=" + accessKey + ";" + "secretKey=" + secretKey
    }

    ##Upload to SQLITE Database - NYPL PATRON DATA
    connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
    cursor = connection.cursor()

    with closing(requests.request("Get",url, headers = headers, stream = True)) as r:
        reader = csv.reader(codecs.iterdecode(r.iter_lines(),'utf-8'), delimiter = ',', quotechar = '"')
        columnList = ["Host","Name","Risk","Description","OS"]
        columnDictionary = {}
        rowDictionary = {}
        print("Organizing",scanName,"data for",creation_date+".....")
        for apiIndex, apiDataRow in enumerate(reader):
            if apiIndex == 0:
                for eltIndex, elt in enumerate(apiDataRow):
                    if elt in columnList:
                        columnDictionary[elt] = eltIndex
                continue
            if apiIndex % 10000 == 0:
                print(apiIndex,"rows processed...")
            rowRiskValue = apiDataRow[columnDictionary["Risk"]]
            rowNameValue = apiDataRow[columnDictionary["Name"]]
            rowHostValue = apiDataRow[columnDictionary["Host"]]
            rowDescriptionValue = apiDataRow[columnDictionary["Description"]]
            rowOSValue = apiDataRow[columnDictionary["OS"]]
            if rowHostValue in rowDictionary:
                rowHostValueDictionary = rowDictionary.get(rowHostValue)
                if rowNameValue not in rowHostValueDictionary:
                    rowHostValueDictionary[rowNameValue] = [creation_date,rowHostValue,rowNameValue,rowRiskValue,rowDescriptionValue,rowOSValue]
            else:
                rowDictionary[rowHostValue] = {}
                rowHostValueDictionary = rowDictionary.get(rowHostValue)
                rowHostValueDictionary[apiDataRow[columnDictionary["Name"]]] = [creation_date,rowHostValue,rowNameValue,rowRiskValue,rowDescriptionValue,rowOSValue]
        try:
            connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
            cursor = connection.cursor()
            print("Uploading",scanName,"data into "+sqlScanName+"_MAP table...")
            for host, nameDict in rowDictionary.items():
                for name, infoList in nameDict.items():
                    cursor.execute("INSERT INTO "+sqlScanName+"_MAP (Scan_Date,Host,Name,Risk,Description,OS)  VALUES(?,?,?,?,?,?)",tuple(infoList))
                connection.commit()
            status = 1
        except Exception as e:
            print("Error:",e)
        finally:
            if status == 0:
                print("Failed to upload all data for:",creation_date)
                #Current sqlHistory: [creation_date,status]
                sqlHistory.append(0) #append ticket_status - should be zero
                # sqlHistory.append(status) #append creation_date for scan_status =, in the query
                sqlHistory = tuple(sqlHistory)
                cursor.execute("DELETE FROM "+sqlScanName+"_HISTORY WHERE [Scan_Date] =?", (creation_date,))
                cursor.execute("INSERT INTO "+sqlScanName+"_HISTORY (Scan_Date,Scan_Status,Tickets_Created) VALUES(?,?,?)",sqlHistory)
                connection.commit()
            elif status == 1:
                print("Successfully uploaded data for:",creation_date)
                sqlHistory.append(0) #append ticket status - should be zero
                sqlHistory[1] = status #scan was successfully created, update Scan_Status
                sqlHistory = tuple(sqlHistory)
                cursor.execute("DELETE FROM "+sqlScanName+"_HISTORY WHERE [Scan_Date] =?", (creation_date,))
                cursor.execute("INSERT INTO "+sqlScanName+"_HISTORY (Scan_Date,Scan_Status,Tickets_Created) VALUES(?,?,?)",sqlHistory)
                connection.commit()
            r.close()


    #Update scanName_History Table
    sqlHistoryDates = []
    cursor.execute("SELECT * FROM "+sqlScanName+"_HISTORY ORDER BY Scan_Date DESC")
    for row in cursor.fetchall():
        sqlHistoryDates.append(row[0])
    for index,creation_date in enumerate(sqlHistoryDates):
        if index < 2:
            print("Keeping entries for:",creation_date)
        else:
            print("Deleting entries for:",creation_date)
            print()
            cursor.execute("DELETE FROM "+sqlScanName+"_MAP WHERE [Scan_Date] =?", (creation_date,))
            cursor.execute("DELETE FROM "+sqlScanName+"_HISTORY WHERE [Scan_Date] =?", (creation_date,))
            connection.commit()
    print()


