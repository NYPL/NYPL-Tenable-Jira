import json

class Config():
    def __init__(self):
        print("Loading Configs...")
        with open (r'..\src\config.json') as configFile:
            self.configData = json.load(configFile)

    #Tenable config getters
    def getTenableAccessKey(self):
        return str(self.configData["Tenable"]["accessKey"])

    def getTenableSecretKey(self):
        return str(self.configData["Tenable"]["secretKey"])

    def getTenableScanName(self):
        return self.configData["Tenable"]["scanName"]

    #Jira config getters
    def getJiraUsername(self):
        return str(self.configData["Jira"]["username"])
    def getJiraPassword(self):
        return str(self.configData["Jira"]["password"])
    def getJiraServer(self):
        return str(self.configData["Jira"]["jiraServer"])
    def getJiraProjectID(self):
        return int(self.configData["Jira"]["projectID"])