from email.mime import base
import logging.handlers
import os
import sys
import re
import json 
#import config
from github import Github 
from github import Repository
from pytablewriter import MarkdownTableWriter

#Errors
from json import JSONDecodeError
from github import GithubException

def main():
    g = Github(os.environ["SOME_SECRET"]) #config.github_secreat
    #g = Github(config.github_secreat) #config.github_secreat
    repo = g.get_repo("pecefulpro/SSF2-MC")
    issue = repo.get_issue(int(sys.argv[1]))
    #issue = repo.get_issue(17)

    if len(issue.labels) > 1:
        send_error("This issue has to many labels on it. Please select the correct Label for your problem.",issue,["Action Pending"])



    if issue.labels[0].name == "Update":
        update_repo(g,repo,issue)

    elif issue.labels[0].name == "Add":
        add_Repo(g,repo,issue)

    elif issue.labels[0].name == "Approved":
        add_Repo(g,repo,issue,True)

    else:
        exit(0)

    

def update_repo(repo,issue):
    repolink = re.search('\\n\\n(.*)\\n\\n', issue.body).group(1)
    version = re.search('Version\\n\\n(.*)\\n\\n', issue.body).group(1)
  

def add_Repo(g,repo,issue,vefied = False):
    
    try:
        repolink = re.search("(?P<url>https?://[^\s]+)", issue.body).group("url")
        repostring = repolink.split("/")
        usersRepo = g.get_repo(repostring[3] + "/" + repostring[4])
    except GithubException:
        send_error("This Repo Does not Exist",issue,[issue.labels[0].name,"Action Pending"])
    except Exception as ex:
        send_error("We could not find your repo",issue,[issue.labels[0].name,"Action Pending"])
    
    master_ref = repo.get_git_ref('heads/main')
    base_tree = repo.get_git_tree(master_ref.object.sha)

    repos = repo.get_collaborators()
    
    if usersRepo.owner.id == issue.user.id:
        pass
    else:
        for r in repos:
            if r.id == issue.user.id:
                break
        send_error("You are not the creator/collaborator of this repo",issue,None,True)

    data = file_checks(usersRepo,issue)

    if data['Info']['Type'] == "Stage":
        contents = repo.get_contents("stages/ml.beta.json")
        minified = json.loads(contents.decoded_content)

        try:
            repodic = {
                "folder-name": data["Stage"]["fileName"],
                "display-name": data["Stage"]["displayName"],
                "type": data['Info']['Type'],
                "commit": usersRepo.get_git_commit(usersRepo.get_git_ref('heads/main').object.sha).sha,
                "version": data["Info"]["Version"],
                "id": usersRepo.id,
                "repository": repolink,
                "description":  data["Stage"]["description"],
                "author": data["Info"]["Creators"]
            }
        except Exception as ex:
            send_error("Your config.json file was missing crucial infomation",issue)
    
        if (vefied is False):
            issue.create_comment("Thank you, your request is now waiting verfication from a staff memeber and will be added soon.")
            issue.edit(labels=["Waiting Verification"])
        else:
            minified["ssf2-mods"].append(repodic)
            mods_array = []
            for d in minified["ssf2-mods"]:
                mods_array.append([
                    d["display-name"],
                    d["author"],
                    d["repository"],
                    d["version"],
                    d["description"]])

            writer = MarkdownTableWriter(
            table_name= "SSF2 Mod Center",
            headers=["Mod name", "Author", "Homepage", "Version", "Description"],
            value_matrix=mods_array,
            margin=1
            )
            #writer.write_table()

            repo.update_file("stages/ml.beta.json","stage json updated", json.dumps(minified,sort_keys=True,indent=4, separators=(',', ': ')),contents.sha)

            mdcontents = repo.get_contents("stages/README.md")
            repo.update_file("stages/README.md","stage read me updated", writer.dumps(),mdcontents.sha)

            

            master_ref = repo.get_git_ref('heads/main')
            base_tree = repo.get_git_tree(master_ref.object.sha)
            
            print(issue.user.name)
            issue.create_comment("Thank you your has been request approved and added.")
            issue.edit(labels=["Approved"],state='closed')
        
    #print(minified)`




def file_checks(repo:Repository,issue):
    try:
        contents = repo.get_contents("src/config.json")
    except GithubException:
        send_error("[Error]: Could not find the config.json file",issue,[issue.labels[0].name,"Action Pending"])
    content = contents.decoded_content

    try:
        minified = json.loads(contents.decoded_content)
    except JSONDecodeError:
        send_error("[Error]: Could not Parse Your config.json file",issue,[issue.labels[0].name,"Action Pending"])
    
    return minified

    

def send_error(error:str,issue,label = None):
    print("error")
    issue.create_comment(error)
    if (label):
        issue.edit(labels=label)
    sys.exit(1)




if __name__ == "__main__":
    main()
