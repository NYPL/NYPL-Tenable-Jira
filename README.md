# NYPL-Tenable-Jira
An automated ticketing system that processes scan reports streamed from Tenable REST APIs, reduces the data via
nested dictionaries, and converts them into tickets through Jira REST APIs
- Processes scan data supplied from Tenable REST APIs and eliminates redundancies via nested dictionaries, then stores this information into a SQL database
- The data is grouped further based on a shared category, typically in scans, that would be the first word of an issue description; on some cases I would customize group names. This is up to your discretion. 
- CSV files 
- Grouped the data further based on a shared category and generated CSV files that captures all hosts pertaining to a
particular issue stemming from a common group via Python
• Built a ticketing system using Jira REST APIs that utilizes the grouped data and CSVs and produced a reduced ticket
load from several thousand to approximately a dozen per scan type via Python and SQL
## Requirements
- Python 3.7 (Do not use Python 3.8!)
- SQLITE 3.24.0

## Dependencies
- backcall==0.1.0
- certifi==2019.11.28
- cffi==1.13.2
- chardet==3.0.4
- colorama==0.4.3
- cryptography==2.8
- decorator==4.4.1
- defusedxml==0.6.0
- filemagic==1.6
- idna==2.8
- ipython==7.10.2
- ipython-genutils==0.2.0
- jedi==0.15.2
- jira==2.0.0
- oauthlib==3.1.0
- parso==0.5.2
- pbr==5.4.4
- pickleshare==0.7.5
- prompt-toolkit==3.0.2
- pycparser==2.19
- pydevd-pycharm==192.6817.19
- Pygments==2.5.2
- PyJWT==1.7.1
- requests==2.22.0
- requests-oauthlib==1.3.0
- requests-toolbelt==0.9.1
- six==1.13.0
- traitlets==4.3.3
- urllib3==1.25.7
- wcwidth==0.1.7

## Configuration details
- Tenable
  - "accessKey": Client key for Tenable API
  - "secretKey": Secret key for Tenable API
  - "scanName": An array-list of scans from Tenable, case sensitive - must match! Use List Scans API if you need them
- Jira
  - "username": Client username for Jira API
  - "password": Client password for Jira API
  - "jiraServer": Client web address for Jira server
  - "projectID" : Server's particular project ID, can be obtained from website

## Authors
- **Arun Ajay** - [@arun-ajay](https://github.com/arun-ajay)

See also the list of [contributors](https://github.com/NYPL/NYPL-Tenable-Jira/graphs/contributors) who participated in this project.

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/NYPL/NYPL-Tenable-Jira/blob/master/LICENSE) file for details

## References
- [Tenable API Reference](https://developer.tenable.com/reference)
- [Jira API Reference](https://jira.readthedocs.io/en/master/)
 
