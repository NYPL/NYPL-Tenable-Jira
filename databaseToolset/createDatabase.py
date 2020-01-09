import sqlite3 #SQLite DB
from src.config import Config #Config load

configInformation = Config()
scanNameList = configInformation.getTenableScanName()
connection = sqlite3.connect(r"..\databases\Tenable_DB.db")
cursor = connection.cursor()
cursor.execute("SELECT name from sqlite_master WHERE type='table';")
tableList = []
flag = False
for table in cursor.fetchall():
    tableList.append(str(table[0]))

for scanName in scanNameList:
    scanName = scanName.replace("-","_") #char sensitivity
    history = scanName + "_HISTORY"
    map = scanName + "_MAP"
    if history not in tableList:
        print("Creating Table:",history)
        cursor.execute("CREATE TABLE " + history + " (\
                        Scan_Date       DATE      PRIMARY KEY,\
                        Scan_Status     BOOLEAN,\
                        Tickets_Created BOOLEAN\
                                            );"
                       )
        flag = True
    if map not in tableList:
        print("Creating Table:",map)
        cursor.execute("CREATE TABLE " + map + " (\
                        Scan_Date   DATE,\
                        Host        TEXT,\
                        Name        TEXT,\
                        Risk        TEXT,\
                        Description TEXT,\
                        OS          TEXT\
                        );"
                       )
        flag = True
if flag == False:
    print("All tables exist for:",tableList)
else:
    print("Database Table Update Complete")
