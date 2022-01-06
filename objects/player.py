class Player:
    def __init__(self, username=None, miiName=None, fc=None,
                 discordObj=None, discordTag=None, canHost=False,
                 mkcID=None, confirmed=False, country=None):
        self.username = username
        self.miiName = miiName
        self.fc = fc
        self.discordObj = discordObj
        self.discordTag = discordTag
        self.canHost = canHost
        self.mkcID = mkcID
        self.confirmed = confirmed
        self.country = country

    def __str__ (self):
        if self.username is not None:
            return self.username
        if self.miiName is not None:
            return self.miiName
        if self.fc is not None:
            return self.fc

    def mkcStr(self):
        return(f"{self.username} | {self.miiName} ({self.fc})")

    def toggleHost(self):
        self.canHost = not self.canHost

    def tableName(self):
        if self.miiName is not None and self.miiName != "":
            name = self.miiName
        #if self.username is not None:
        else:
            name = self.username
        if name.startswith("#"):
            name = "." + name
        #brackets are problematic for table format so we replace them
        name = name.replace('[', '(')
        name = name.replace(']', ')')
        #byte order marks can cause some unwanted trouble
        #so we remove those too
        name = name.replace('\ufeff', '')
        name = name.replace('\ufffe', '')
        return name
