class Character:
    name = ""
    factionid = 0
    keywords = []
    path = ""

    def __init__(self, name, factionid, keywords=[]):
        self.name = name
        self.factionid = factionid
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
        if "," in text:
            trimmed = text.replace(' ', '').replace(',', ' ')
            charKeys = " ".join(trimmed.split()).split(' ')
        else:
            charKeys = " ".join(text.split()).split(' ')
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

class Faction:
    id = 0
    title = ""

    def __init__(self, id, title):
        self.id = id
        self.title = title
