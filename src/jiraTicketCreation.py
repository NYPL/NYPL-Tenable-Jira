import sqlite3
import csv
from jira import JIRA
import requests
from src.config import Config
import os.path
import time

configInformation = Config()
scanNameList = configInformation.getTenableScanName()
connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
cursor = connection.cursor()
scanTicketMap = {}
for scanName in scanNameList:
    if scanName not in scanTicketMap:
        scanTicketMap[scanName] = 0
    print()
    print("Creating tickets for",scanName)
    print()
    sqlScanName = scanName.replace("-", "_")
    #Get latest ticket Scan_Date
    cursor.execute("SELECT * FROM "+sqlScanName+"_HISTORY ORDER BY Scan_Date DESC")
    row = cursor.fetchone()
    creation_date = row[0]
    tenableStatus = row[1]
    if tenableStatus == 0:
        print("Mapping failed for",scanName,"on",creation_date,"retry again.")
        continue
    print(creation_date)
    #Get data of latest Scan_Date (Critical or High only)
    cursor.execute("SELECT * FROM "+sqlScanName+"_MAP WHERE Scan_Date = ? AND (Risk = 'Critical' or Risk = 'High') ORDER BY NAME",(creation_date,))


    #Initialize empty hashmap of issues
    groupDictionary = {}

    #Go through each row
    for index, row in enumerate(cursor.fetchall()):
        #names are full problem name, group encompasses multiple names
        #Collect name and host
        name = row[2]
        host = row[1]
        group = ''
        #Renaming of certain names
        if name.startswith("KB"):
            group = "KB"
        elif name.startswith("MS"):
            group = "MS"
        elif name.startswith("Mozilla") or name.startswith("Firefox"):
            group = "Mozilla"
        elif name.startswith("Oracle") or name.startswith("Sun"):
            group = "Oracle"
        elif name.startswith("Insecure") or name.startswith("Windows"):
            group = "Windows"
        #Catch-all of groups, gets only first word
        else:
            group = name.split()[0]
            if group == "Security":
                group = "Security Update"
        #Updating groupDictionary hashmap (key = group, value = hashmap --> key = name, value = host)
        if group not in groupDictionary:
            groupDictionary[group] = {}
            nameDictionary = groupDictionary[group]
            if name not in nameDictionary:
                nameDictionary[name] = [host]
            else:
                nameDictionary[name].append(host)
        else:
            nameDictionary = groupDictionary[group]
            if name not in nameDictionary:
                nameDictionary[name] = [host]
            else:
                nameDictionary[name].append(host)

    #Counts unique # of problems for description
    count = 0
    for name,l in groupDictionary.items():
        for val in l:
            count += 1

    username = configInformation.getJiraUsername()
    password = configInformation.getJiraPassword()
    projectID = configInformation.getJiraProjectID()

    server = configInformation.getJiraServer()
    print("Total # of problem groups:",len(groupDictionary.keys()))
    print("Total distinct problems from all groups combined",count)
    options = {"server": server}
    jira = JIRA(options, basic_auth=(username, password))
    print("Beginning Ticket Creation Process...")

    #Start creating CSVs of each problem group
    ticketCount = 0
    for group,namedict in groupDictionary.items(): #get each namedict
        filename = '..\csv\\' + group + '.csv'
        # filename = './csv/'+group+'.csv'
        count = 0
        with open(filename,'w',newline='') as file:
            writer = csv.writer(file)
            for name,hostList in namedict.items(): #start writing each row in CSV
                if count == 0:
                    writer.writerow(["Issue","Host"])
                count += 1
                hostCount = 0
                for host in hostList:
                    writer.writerow([name,host])
        file.close()
        created = False #assume a ticket does not exist
        #Start searching through all of the issues
        blockSize = 100
        blockNum = 0
        while True:
            startIndex = blockNum*blockSize
            issuesList = jira.search_issues(jql_str='',startAt=startIndex,maxResults=blockSize) #search all jira issues
            #Reached end of issue search
            if len(issuesList) == 0:
                break
            #If we do find it, update the csv file and description
            for issue in issuesList:
                if (issue.raw['fields']["summary"] == group and (scanName in issue.raw['fields']['labels']) and ("Tenable" in issue.raw['fields']['labels'])):
                    if (issue.raw['fields']["customfield_10202"] == creation_date):
                        print(group, "already exists and has latest entry. Skipping.")
                        created = True
                        break
                    print(group,"is outdated. Updating ticket...")
                    issueObj = jira.issue(issue.key)
                    for attachment in issueObj.fields.attachment:
                        jira.delete_attachment(attachment.id)
                    issueObj.update(notify=False, description=(str(count) + " unique problems as of " + creation_date))
                    # issueObj.update(notify=False, fields={"customfield_10202":creation_date})
                    jira.add_attachment(issueObj,filename,filename=group+".csv")
                    ticketCount += 1
                    created = True
                    break
            blockNum += 1
            if created == True:
                break
        #If we don't find the group, create a new ticket
        if created == False:
            print(group, "is new. Creating new ticket...")
            issuedict = {}
            issuedict['project'] = {'id': projectID}
            issuedict['summary'] = group
            issuedict['description'] = str(count) + " unique problems as of " + creation_date
            issuedict['issuetype'] = {'name': 'Bug'}
            issuedict['priority'] = {'name': 'Highest'}
            issuedict['labels'] = [scanName,"Tenable"]
            # issuedict['customfield_10202'] = creation_date #Scan Date custom field
            issue = jira.create_issue(fields = issuedict)
            # issue.update(fields={"labels":["Tenable",scanName]})
            issueID = issue.id
            url = server + "/rest/api/latest/issue/"+issueID+"/attachments"
            headers = {"X-Atlassian-Token": "nocheck"}
            files = {"file": open(filename,"rb")}
            r = requests.post(url,auth=(username,password), files=files, headers=headers)
            ticketCount += 1
    #Delete CSV Files
    csvpath = "..\csv"
    for root, dirs, files in os.walk(csvpath):
        for file in files:
            if file != ".gitkeep":
                os.remove(os.path.join(root, file))
    scanTicketMap[scanName] = ticketCount
connection.close()
totalTicketCount = 0
print()
for scan,count in scanTicketMap.items():
    print("Scan:",scan,"\tTickets Created:",count)
    totalTicketCount += count
print("Total Tickets Created:",totalTicketCount)