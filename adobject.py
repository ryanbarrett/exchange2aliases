class adobject:

  def __init__(self):
    self.members = []
    self.proxyAddresses = []

  def __str__(self):
    return "name:%s, mail:%s, mailNickname:%s, MemberCount:%s" %(self.name,self.mail,self.mailNickname,str(len(self.members)))
  
  def name(self,name):
    self.name = name

  def mail(self,mail):
    self.mail = mail
  
  def add_proxyAddress(self,proxyAddress): #alternate aliases
    self.proxyAddresses.append(proxyAddress)

  def mailNickname(self,mailNickname):
    self.mailNickname = mailNickname
  
  def altRecipient(self,altRecipient):
    self.altRecipient = altRecipient
  
  def altRecipientMail(self,altRecipientMail):
    self.altRecipientMail = altRecipientMail

  def add_member(self,member):
    self.members.append(member)


class adobjectlist:

  def __init__(self):
    self.adobjects = {}

  def add_adobject(self,adobject):
    self.adobjects[adobject.name] = adobject
  
  def __iter__(self):
    return self.adobjects
