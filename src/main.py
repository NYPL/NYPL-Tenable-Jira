
if __name__ == "__main__":
    print("--------------------\nInitializing Database Update")
    import databaseToolset.createDatabase
    print("--------------------\nInitializing Tenable Data Collection Process \n")
    import src.tenableDataHashmap
    print("\nData collection hashmap Complete\n--------------------")
    print("Initializing Jira Ticket Creation Process \n")
    import src.jiraTicketCreation
    print("\nSuccess")
