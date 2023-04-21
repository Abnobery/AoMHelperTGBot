class Character:
    name = ""
    keywords = []
    path = ""

    def __init__(self, name, keywords = []):
        self.name = name
        self.keywords = keywords
        self.path = f'images/chars/{name}.png'

class CharacterTeam:
    members: list[str] = []

    def __init__(self, members):
        self.members = members

    def __eq__(self, other):
        if isinstance(other, CharacterTeam):
            thisMembers = list(self.members[0]) + sorted(self.members[1:])
            otherMembers = list(other.members[0]) + sorted(other.members[1:])
            return thisMembers == otherMembers
        return False

    def charName(c):
        return c.name

    def teamFromChars(chars: list[Character]):
        return CharacterTeam(list(map(CharacterTeam.charName, chars)))

    def characterTeamFromText(text):
        trimmed = text.replace(',', ' ')
        charKeys = " ".join(trimmed.split()).split(' ')
        charsList = []
        for charKey in charKeys:
            char = CharProvider.charByKey(charKey)
            if char != None:
                charsList.append(char.name)
        if len(charsList) == 5:
            return CharacterTeam(charsList)
        else:
            return None

CharacterTeam.characterTeamFromText = staticmethod(CharacterTeam.characterTeamFromText)

class CharacterTeamRecord:
    team: CharacterTeam = {}
    counterTeams: list[CharacterTeam] = []

    def __init__(self, team, counterTeams = []):
        self.team = team
        self.counterTeams = counterTeams

    def __eq__(self, other):
        if isinstance(other, CharacterTeamRecord):
            return self.team == other.team
        return False

class CharProvider:
    definition = [
            Character("rok", ["rok", "рок", "енот"]),
            Character("dexxa", ["dexxa", "декса"]),
            Character("crowley", ["crowley", "кроули"]),
            Character("katar", ["katar", "катар"]),
            Character("irazzt", ["irazzt", "ираззт"]),
            Character("balthazar", ["balthazar", "бальтазар"]),
            Character("liongo", ["liongo", "лионго"]),
            Character("mordred", ["mordred", "мордред"]),
            Character("morrigan", ["morrigan", "морриган"]),
            Character("belladonna", ["belladonna", "белладонна"]),
            Character("kromme", ["kromme", "кромм"]),
            Character("nora", ["nora", "нора"]),
            Character("firar", ["firar", "фирар"]),
            Character("elios", ["elios", "элиос"]),
            Character("librarian", ["librarian", "библиотекарь"]),
            Character("tiros", ["tiros", "тирос"]),
            Character("sacrif", ["sacrif", "сакриф"]),
            Character("magnus", ["magnus", "магнус"]),
            Character("azariel", ["azariel", "азариэль"]),
            Character("tsuna", ["tsuna", "цуна"]),
            Character("lokhir", ["lokhir", "локхир"]),
            Character("roinar", ["roinar", "ройнар", "роинар"]),
            Character("drake", ["drake", "дрейк", "дреик"]),
            Character("llael", ["llael", "ллаэль"]),
            Character("phoenix", ["phoenix", "жар-птица", "феникс", "птица"]),
            Character("zhubajie", ["zhubajie", "чжу бацзе", "свинья"]),
            Character("vilarr", ["vilarr", "виларр"]),
            Character("artus", ["artus", "артус"]),
            Character("naja", ["naja", "найя", "наия"]),
            Character("wukong", ["wukong", "сунь укун", "укун", "обезьяна"]),
        ]

    def charByKey(key):
        return next((x for x in CharProvider.definition if any(item.startswith(key.lower()) for item in x.keywords)), None)

CharProvider.charByKey = staticmethod(CharProvider.charByKey)
CharacterTeam.teamFromChars = staticmethod(CharacterTeam.teamFromChars)
CharacterTeam.charName = staticmethod(CharacterTeam.charName)
