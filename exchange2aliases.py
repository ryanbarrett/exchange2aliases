#!python



##csvde -f test.csv


import csv,argparse
from sys import stdin
from adobject import adobject
from adobject import adobjectlist

argparser = argparse.ArgumentParser(description='Arguments that may be parsed.',epilog="Example: ad2aliases.py -f adfile.csv -d test.com")
argparser.add_argument('--csvfile','-f',type=str,required=True,help='The CSV file generated with "csvde -f adfile.csv"')
#argparser.add_argument('--proxyAddresses','-pa',action='store_true',help='Include proxy addresses in aliases if different mail/domains are included')
#argparser.add_argument('--domain','-d',type=str,required=True,help='The Domain for the target system')
argparser.add_argument('--outfile','-o',default="aliases",type=str,help='outfile if required, otherwise will output as "aliases"')
args = argparser.parse_args()


#Main Functions
def BuildADObjects(csvfile):
  #pull mail, mailNickname, members, memberOf into a Group Object
  ActDirObj = {}
  with open(csvfile) as csvf:
    # Reads from the file specified with --csvfile 
    reader = csv.DictReader(csvf)
    for row in reader:
      ado = adobject()
      # name contains the CN name, the name that is referenced by member and altRecipient.
      ado.name = row['cn']
      # object class contains the class: User, Group, or Contact
      ado.objectClass = row['objectClass']
      # mailNickname contains something... not sure why this was included....
      ado.mailNickname = row['mailNickname']
      # mail contains the email address mail is being sent to on this server (i.e. the alias that would be created)
      ado.mail = row['mail'].lower()
      # altRecipient contains a contact or another user that this emial account is forwarded to.
      ado.altRecipient = ReturnCN(row['altRecipient'])
      # member contains a list of members for a group
      members = ReturnCNfromMemberList(row['member']) #Returns a list of members if the record is a group
      for member in members:
        ado.add_member(member)
      # ProxyAddresses are alternate addresses for a user or group.
      # smtp:user01@test.com;smtp:user@test.com;X400:c=us\;a= \;p=Test\;o=Exchange\;s=User\;
      proxyAddresses = row['proxyAddresses'].split(";")  #
      SetproxyAddresses(ado,proxyAddresses)
      if ado.objectClass == "user" or ado.objectClass == "contact" or ado.objectClass == "group":
        ActDirObj[ado.name]=ado
  ActDirObj = SetAltRecipientMail(ActDirObj)
  ActDirObj = RemoveAnyWithoutEmail(ActDirObj)
  return ActDirObj

def SetAltRecipientMail(ActDirObj):
  for adobj in list(ActDirObj.values()):
    if adobj.altRecipient:  #Indicates a an alternate email address exists.
      ActDirObj[adobj.name].altRecipientMail = ReturnOneEmail(ActDirObj,adobj.altRecipient)
  return ActDirObj

def BuildAliases(ActDirObj):
  aliases = []
  galiases = []
  ualiases = []
  badaliases = []
  for adobj in list(ActDirObj.values()):
    BadAlias = False
    if len(adobj.members) > 0 and adobj.members[0] != None and adobj.objectClass == "group":  #Indicates a group when the members are greater than 1
      alias = adobj.mail.split("@")[0] #strip the domain
      emailaddresses = ReturnMemberEmailAddresses(ActDirObj,adobj.members) #return the email addresses for the members in the group
      addrs=""
      for e in emailaddresses:
        if type(e) is str and e != "":
          if addrs == "":
            addrs=e
          else:
            addrs+=","+e
      galiases.append("\n\n# "+adobj.objectClass+" '"+adobj.name+"' \n")
      galiases.append(alias+":"+addrs+"\n")
      BadAlias = False
    else:
      BadAlias = True
    if type(adobj.altRecipientMail) is str and adobj.altRecipientMail != "":#indicates an account with an alternate email address
      ualiases.append("\n\n# "+adobj.objectClass+" '"+adobj.name+"' \n")
      alias = adobj.mail.split("@")[0] #strip the domain
      ualiases.append(alias+":"+adobj.altRecipientMail+"\n")
      BadAlias = False
    else:
      BadAlias = True
    if len(adobj.proxyAddresses) > 0 and adobj.proxyAddresses != None:
      for e in adobj.proxyAddresses:
        print("pAlias "+e)
        if adobj.objectClass == "group":
          galiases.append(e+":"+adobj.mail.split("@")[0]+"\n")
        if adobj.objectClass == "user":
          ualiases.append(e+":"+adobj.mail.split("@")[0]+"\n")
      BadAlias = False
    else:
      BadAlias = True
    if BadAlias:
      if type(adobj.name) is str and adobj.name != "":
        badaliases.append("\n# "+adobj.objectClass+"'"+adobj.name+"' No Mail data found \t\t\t"+','.join(map(str,adobj.members)).strip("None"))
  #aliases.append("#Groups "+str(len(galiases)))
  aliases.append("#Groups ")
  for ga in galiases:
    aliases.append(ga)
  #aliases.append("\n\n\n#Users "+str(len(ualiases)))
  aliases.append("\n\n\n#Users ")
  for ua in ualiases:
    aliases.append(ua)
  aliases.append("\n\n\n#Bad Aliases "+str(len(badaliases)))
  for ba in badaliases:
    aliases.append(ba)
  return aliases

def WriteOutaliasesfile(outfile,aliases):
  # writes out the file specified with --outfile
  f = open(outfile,'w')
  f.write(aliases)
  f.close()




#supporting functions

def SetproxyAddresses(ado,proxyAddresses):
  for proxyAddress in proxyAddresses:
    if ado.objectClass != "contact" and "smtp:" in proxyAddress:
      p = proxyAddress.replace('smtp:','').split("@")
      #print("if "+p[0]+" doesnotequal "+ado.mail.split("@")[0])
      if p[0].lower() != ado.mail.split("@")[0].lower() and p[0] not in ado.proxyAddresses: #if alternate email addresses do not match the username, add as a proxy
        #print("Adding "+ p[0])
        ado.add_proxyAddress(p[0].lower())
  #return ado

def RemoveAnyWithoutEmail(ActDirObj):
  cleanActDirObj = {}
  for adobj in ActDirObj.values():
    if type(adobj.mail) is str and adobj.mail != "" or type(adobj.altRecipientMail) is str and adobj.altRecipientMail != "":
      cleanActDirObj[adobj.name]=adobj
  return cleanActDirObj

def ReturnCNfromMemberList(data):
  members = []
  splitmembers = data.split(";")
  for member in splitmembers:
    members.append(ReturnCN(member))
  return members

def ReturnCN(member):  #strips and returns only the value of CN=
  for m in member.split(","):
      if "CN=" in m:
        return m.replace("CN=","")

def ReturnMemberEmailAddresses(ActDirObj,membersnames): #gets multiple email addresses from a list.
  emailaddresses = []
  for membername in membersnames:
    try:
      adobj = ActDirObj[membername] #look in the main object dictionary for a member and return that object
      if type(adobj.altRecipientMail) is str and adobj.altRecipientMail != "":
        emailaddresses.append(adobj.altRecipientMail)
      elif type(adobj.mail) is str and adobj.mail != "":
        emailaddresses.append(adobj.mail)
    except Exception, e:
      pass
  return emailaddresses

def ReturnOneEmail(ActDirObj,name):
  emailaddress = ""
  try:
    emailaddress = ActDirObj[name].mail
    #print emailaddress
  except Exception, e:
    pass
  return emailaddress


def str2bool(v):
  return v.lower() in ("yes", "y")








def main(args):
  ActDirObj = BuildADObjects(args.csvfile)
  #for adobj in ActDirObj:
  #  print adobj.mail,adobj.mailNickname
  #  print "  ",adobj.members
  aliases = BuildAliases(ActDirObj)
  aliasesstring = ""
  for aliasline in aliases:
    aliasesstring += aliasline
  #isWriteOutFileOK = stdin.readline("Does the File Look Alright to write to aliases? y/n")
  #if str2bool(isWriteOutFileOK):
  #  print("writing out aliases file...")
  WriteOutaliasesfile(args.outfile,aliasesstring)
  #  print("Done, bye.")


if __name__ == "__main__":
  try:
    main(args)
  except(Exception):
    raise
  else:
    pass
  finally:
    pass
