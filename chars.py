class Character:
    name = ""
    keywords = []
    path = ""

    def __init__(self, name, keywords=[]):
        self.name = name
        self.keywords = keywords
        self.path = f'images/chars/{name}.png'


class CharacterTeam:
    members: list[str] = []

    def __init__(self, members):
        self.members = members

    def __eq__(self, other):
        if isinstance(other, CharacterTeam):
            thisMembers = [self.members[0]] + sorted(self.members[1:])
            otherMembers = [other.members[0]] + sorted(other.members[1:])
            return thisMembers == otherMembers
        return False

    @staticmethod
    def charName(c):
        return c.name

    @staticmethod
    def teamFromChars(chars: list[Character]):
        return CharacterTeam(list(map(CharacterTeam.charName, chars)))

    @staticmethod
    def characterTeamFromText(storageEntity, text):
        trimmed = text.replace(',', ' ')
        charKeys = " ".join(trimmed.split()).split(' ')
        charsList = []
        for charKey in charKeys:
            char = storageEntity.charByKey(charKey)
            if char != None:
                charsList.append(char.name)
        if len(charsList) == 5:
            return CharacterTeam(charsList)
        else:
            return None


class CharacterTeamRecord:
    team: CharacterTeam = {}
    counterTeams: list[CharacterTeam] = []

    def __init__(self, team, counterTeams=[]):
        self.team = team
        self.counterTeams = counterTeams

    def __eq__(self, other):
        if isinstance(other, CharacterTeamRecord):
            return self.team == other.team
        return False
