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
    reader = csv.DictReader(csvf)
    for row in reader:
      ado = adobject()
      ado.name = row['cn']
      ado.objectClass = row['objectClass']
      ado.mailNickname = row['mailNickname']
      ado.mail = row['mail']
      ado.altRecipient = ReturnCN(row['altRecipient'])
      members = ReturnCNfromMemberList(row['member']) #Returns a list of members if the record is a group
      for member in members:
        ado.add_member(member)
      #proxyAddresses = row['proxyAddresses'].split(";")
      #for proxyAddress in proxyAddresses:
      #  if "smtp:" in proxyAddress:
      #    ado.add_proxyAddress(proxyAddress.strip('smtp:'))
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
      galiases.append("\n# "+adobj.objectClass+"'"+adobj.name+"' \n")
      galiases.append(alias+":"+addrs+"\n")
    elif type(adobj.altRecipientMail) is str and adobj.altRecipientMail != "":#indicates an account with an alternate email address
      ualiases.append("\n# "+adobj.objectClass+"'"+adobj.name+"' \n")
      alias = adobj.mail.split("@")[0] #strip the domain
      ualiases.append(alias+":"+adobj.altRecipientMail+"\n")
    #elif len(adobj.proxyAddresses) > 1:
    #  for e in adobj.proxyAddresses:
    #    if e.split("@")[0] == adobj.mail.split("@")[0]:
    #      aliases.append(e+":"+adobj.mail+"\n")
    else:
      if type(adobj.name) is str and adobj.name != "":
        badaliases.append("\n# "+adobj.objectClass+"'"+adobj.name+"' No Mail data found \t\t\t"+','.join(map(str,adobj.members)).strip("None"))
  aliases.append("#Groups")
  for ga in galiases:
    aliases.append(ga)
  aliases.append("#Users")
  for ua in ualiases:
    aliases.append(ua)
  aliases.append("#Bad Aliases")
  for ba in badaliases:
    aliases.append(ba)
  return aliases

def WriteOutaliasesfile(outfile,aliases):
  f = open(outfile,'w')
  f.write(aliases)
  f.close()




#supporting functions

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
