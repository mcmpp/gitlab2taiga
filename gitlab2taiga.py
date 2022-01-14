#!/usr/bin/env python3

import ujson
import pandas as pd
import requests
import json
import sys, getopt
import getpass
import validators

ENDPOINT_PROJECTS = "/api/v1/projects"
ENDPOINT_MEMBERS = "/api/v1/memberships"
ENDPOINT_ROLES = "/api/v1/roles"
ENDPOINT_LOGIN = "/api/v1/auth"
ENDPOINT_USERSTORIES = "/api/v1/userstories"
ENDPOINT_USERSTORIES_STATUS = "/api/v1/userstory-statuses"

def main(argv):
    try:
        opts, args = getopt.getopt(argv,'hi:m:e:u:p:')
    except getopt.GetoptError:
        print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        sys.exit(2)
    if len(opts) != 5:
        print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        sys.exit(2)
    else:
        for opt, arg in opts:
            if opt == '-h':
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
                sys.exit()
            elif opt in '-i':
                issues_file = arg
            elif opt in '-m':
                members_file = arg
            elif opt in '-e':
                endpoint = arg
            elif opt in '-u':
                username = arg
            elif opt in '-p':
                projectName = arg
            else:
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        if (username is not None) and (issues_file is not None) and (members_file is not None) and (endpoint is not None) and (projectName is not None):
            if (validators.url(endpoint)):
                getAccessToken(username, endpoint)
                createProject(endpoint, projectName)
                getAllUserStoryStatus(endpoint)
                createMemberships(endpoint, members_file)
                createHashMapGitlabUserIdTaiga(members_file, endpoint)
                createUserStory(issues_file, endpoint)
                #deleteAllUserStories(endpoint)
            else:
                print ('The endpoint provided is not a valid url')
                exit (2)
        else:
            print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')

def getAccessToken(username, endpoint):
    print('Please, introduce the password to connect to taiga username already provided')
    global password
    password = getpass.getpass()
    data = {}
    data['password'] = password;
    data['type'] = 'normal';
    data['username'] = username;
    response = requests.post(endpoint + ENDPOINT_LOGIN, data = data)
    if response.ok:
        responseJson = response.json()
        try:
            global authToken
            authToken = responseJson['auth_token']
            print ('Auth token request successful')
        except:
            print ('We could not get the authorization token from the login request')
            exit (2)
    else:
        print ('The response from the server is not valid')
        exit (2)

def prepareHeaders():
    if (authToken is not None):
        return {"Authorization": "Bearer " + authToken , "x-disable-pagination": "True" }
    else:
        print ('The auth token is not correct')
        exit (2)

# ----------------   MEMBERSHIPS

def getMembershipsFullName(endpoint):
    response = requests.get(endpoint + ENDPOINT_MEMBERS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            memberName = []
            for membership in responseJson:
                memberName.append(membership['full_name'])
            print ('Current memberships are: ' , memberName)
            return memberName
        except:
            print ('We could not get the memberships full name')
    else:
        print ('The response from the server is not valid')
        exit (2)

def getMembershipEmail(membershipId,endpoint):
    response = requests.get(endpoint + ENDPOINT_MEMBERS + '/' + str(membershipId), headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            return responseJson['email']
        except:
            print ('We could not get the memberships email')
    else:
        print ('The response from the server is not valid')
        exit (2)

def createHashMapGitlabUserIdTaiga(members_file, endpoint):
    records = map(ujson.loads, open(members_file, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    gitlabUsers = df[['user']].values.tolist()
    gitlabUserDict = dict()
    for gitlabUser in gitlabUsers:
        gitlabUserDict[gitlabUser[0]['id']] = gitlabUser[0]['username']
    for key, value in gitlabUserDict.items():
        response = requests.get(endpoint + ENDPOINT_MEMBERS, headers = prepareHeaders())
        if response.ok:
            responseJson = response.json()
            try:
                global gitlabTaigaUsersDict
                gitlabTaigaUsersDict = dict()
                for membership in responseJson:
                    if getMembershipEmail(membership['id'], endpoint) == value + '@tegonal.com':
                        gitlabTaigaUsersDict[membership['user']] = key
            except:
                print ('We could not get the memberships full name')
        else:
            print ('The response from the server is not valid')
            exit (2)
#        taigaUserId =
#        gitlabUserMapTaigaUser[user] =

def getMembershipsFromGitlabFile(members_file, endpoint):
    records = map(ujson.loads, open(members_file, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    users = df[['user','access_level']]
    values = []
    for user in users.values.tolist():
        if (int(user[1]) >= 40):
            data = {}
            data['project'] = projectId
            data['username'] = user[0]['username'] + '@tegonal.com'
            data['role'] = getStakeholderRole(endpoint)
            values.append(data)
    return(values)

def createMemberships(endpoint, members_file):
    memberships = getMembershipsFromGitlabFile(members_file, endpoint)
    for member in memberships:
        if not membershipExists(endpoint, member['username']):
            response = requests.post(endpoint + ENDPOINT_MEMBERS, data = member, headers = prepareHeaders())
            if response.ok:
                print ('Member ', member['username'], ' created')
            else:
                print ('The response from the server while creating the memberships is not valid')
                exit (2)
        else:
            print ('The member ', member['username'], ' already exists')

def membershipExists(endpoint, memberName):
    memberIds = getMembershipIds(endpoint, memberName)
    for memberId in memberIds:
        response = requests.get(endpoint + ENDPOINT_MEMBERS + '/' + str(memberId), headers = prepareHeaders())
        if response.ok:
            responseJson = response.json()
            try:
                if responseJson['email'] == memberName:
                    return True
            except:
                print ('We could not get the member email')
        else:
            print ('The response from the server is not valid')
            exit (2)
    return False

def getMembershipIds(endpoint, memberName):
    response = requests.get(endpoint + ENDPOINT_MEMBERS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            memberIds = []
            for membership in responseJson:
                memberIds.append(membership['id'])
            return memberIds
        except:
            print ('We could not get the member id')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  ROLES

def getStakeholderRole(endpoint):
    response = requests.get(endpoint + ENDPOINT_ROLES + '?project=' + str(projectId), headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            for role in responseJson:
                if role['name'] == 'Stakeholder':
                    return role['id']
        except:
            print ('We could not get the roles')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  PROJECT

def createProject(endpoint, projectName):
    global projectId
    projectId = projectNameExists(endpoint, projectName)
    if projectId == 0:
        data = {}
        data['description'] = "Gitlab import from " + projectName
        data['name'] = projectName
        response = requests.post(endpoint + ENDPOINT_PROJECTS, data = data, headers = prepareHeaders())
        if response.ok:
            responseJson = response.json()
            projectId = responseJson['id']
            print ('The project ' , projectName , ' with id= ' , projectId , 'has been created')
        else:
            print ('The response from the server is not valid')
            exit (2)
    else:
        print ('The project already exists')

def projectNameExists(endpoint, projectName):
    response = requests.get(endpoint + ENDPOINT_PROJECTS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            for project in responseJson:
                if project['name'] == projectName:
                    return project['id']
            return 0
        except:
            print ('We could not get the project name')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  ISSUES

def getIssuesFromGitlabFile(endpoint, issues_file):
    records = map(ujson.loads, open(issues_file, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    issues = df[['title','description','state','notes', 'author_id', 'issue_assignees']]
    values = []
    for issue in issues.values.tolist():
        data = {}
        if gitlabTaigaUsersDict.get('5'):
            data['assigned_to'] = gitlabTaigaUsersDict.get('5')
        data['subject'] = issue[0]
        data['description'] = issue[1]
        data['description_html'] = issue[1]
        if (issue[2] == 'blocked'):
            data['is_blocked'] = True
        else:
            data['is_blocked'] = False
        if (issue[2] == 'closed'):
            data['is_closed'] = True
            #this status needs to be variable
            data['status'] = userStoryStatuses.get('Archived')
        else:
            data['is_closed'] = False
            #this status needs to be variable
            data['status'] = userStoryStatuses.get('Ready')
        if gitlabTaigaUsersDict.get('4'):
            data['owner'] = gitlabTaigaUsersDict.get('4')
        data['project'] = projectId
        data['notes'] = issue[3]
        values.append(data)
    return (values)

# ----------------  ISSUES

def createUserStory(issues_file, endpoint):
    issues = getIssuesFromGitlabFile(endpoint, issues_file)
    for issue in issues:
        response = requests.post(endpoint + ENDPOINT_USERSTORIES, data = issue, headers = prepareHeaders())
        print ('The user story ', issue['subject'],' has been created')
        if response.ok:
            responseJson = response.json()
            notes = issue['notes']
            cnt = 0
            for note in notes:
                data = {}
                data['comment']= note['note']
                data['version']= cnt + 1
                response = requests.patch(endpoint + ENDPOINT_USERSTORIES + '/' + str(responseJson['id']),data = data, headers = prepareHeaders())
                print ('A comment has been added to the user story ', issue['subject'])
        else:
            print ('The response from the server while creating the user story is not valid')
            exit (2)

def deleteAllUserStories(endpoint):
    userStoryIds = getAllUserStoryIds(endpoint)
    for userStoryId in userStoryIds:
        response = requests.delete(endpoint + ENDPOINT_USERSTORIES + '/' + str(userStoryId), headers = prepareHeaders())
        if response.ok:
            print ('User Story ', userStoryId, ' deleted')
        else:
            print ('The response from the server while deleting the user story is not valid')
            exit (2)


def getAllUserStoryIds(endpoint):
    response = requests.get(endpoint + ENDPOINT_USERSTORIES + '?project=' + str(projectId), headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            userStoriesId = []
            for userStory in responseJson:
                userStoriesId.append(userStory['id'])
            return userStoriesId
        except:
            print ('We could not get the userStories')
    else:
        print ('The response from the server is not valid')
        exit (2)


# ----------------  USER STORIES STATUS

def getAllUserStoryStatus(endpoint):
    response = requests.get(endpoint + ENDPOINT_USERSTORIES_STATUS + '?project=' + str(projectId), headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            global userStoryStatuses;
            userStoryStatuses = dict()
            for userStoryStatus in responseJson:
                userStoryStatuses[userStoryStatus['name']] = userStoryStatus['id']
        except:
            print ('We could not get the userStories')
    else:
        print ('The response from the server is not valid')
        exit (2)


if __name__ == "__main__":
   main(sys.argv[1:])
