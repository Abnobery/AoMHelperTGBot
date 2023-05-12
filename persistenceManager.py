from sqlalchemy import create_engine, ForeignKey, func
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from chars import Character, CharacterTeamRecord, CharacterTeam
import logging

Base = declarative_base()
logging.basicConfig(level=logging.INFO)

class StorageEntity:
    characters: list[Character] = []
    teams: list[CharacterTeamRecord] = []

    def __init__(self, characters, teams = []):
        self.teams = teams
        self.characters = characters

    def charByKey(self, key):
        return next(
            (x for x in self.characters if any(item.startswith(key.lower()) for item in x.keywords)), None)

    def charsFromKeys(self, keys):
        return list(map(self.charByKey, keys))

class DbChar(Base):
    __tablename__ = "chars"
    charname = Column(String, primary_key=True, nullable=False)

class DbKeyword(Base):
    __tablename__ = "char_keywords"
    keyword = Column(String, primary_key=True, nullable=False)
    charname = Column(String, ForeignKey("chars.charname"), nullable=False)

class DbTeam(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, nullable=False)
    leader = Column(String, ForeignKey("chars.charname"), nullable=False)
    slot2 = Column(String, ForeignKey("chars.charname"), nullable=False)
    slot3 = Column(String, ForeignKey("chars.charname"), nullable=False)
    slot4 = Column(String, ForeignKey("chars.charname"), nullable=False)
    slot5 = Column(String, ForeignKey("chars.charname"), nullable=False)

class DbTeamCounters(Base):
    __tablename__ = "counter_teams"
    id = Column(Integer, primary_key=True, nullable=False)
    targetteamid = Column(Integer, ForeignKey("teams.id"), nullable=False)
    counterteamid = Column(Integer, ForeignKey("teams.id"), nullable=False)

class PersistenceManager:
    storage: sessionmaker
    def __init__(self, db):
        local_session = sessionmaker(autoflush=False,
                                     autocommit=False, bind=create_engine(db))
        self.storage = local_session()

    def addCharacter(self, character: Character):
        try:
            notexists = self.storage.query(DbChar).filter_by(charname=character.name).first() is None
            if notexists:
                dbChar = DbChar(charname=character.name)
                self.storage.add(dbChar)
                for keyword in character.keywords:
                    keywordnotexists = self.storage.query(DbKeyword).filter_by(charname=keyword, keyword=character.name).first() is None
                    if keywordnotexists:
                        dbKeyword = DbKeyword(keyword=keyword, charname=character.name)
                        self.storage.add(dbKeyword)
                self.storage.commit()
                logging.info(f'successfully added character {character.name} with keywords')
        except Exception as ex:
            logging.error(f'error: addCharacter: {ex}')


    def getAllCharacters(self):
        try:
            chars = self.storage.query(DbChar.charname).all()
            charnames = [charname[0] for charname in chars]
            charList: list[Character] = []
            for char in charnames:
                keywords = self.storage.query(DbKeyword.keyword).filter(DbKeyword.charname == char).all()
                keywordsStr = [keyword[0] for keyword in keywords]
                charList.append(Character(char, keywordsStr))
            return charList
        except Exception as ex:
            logging.error(f'error in retrieving characters: {ex}')
            return []

    def addCharacterTeam(self, characterTeam: CharacterTeam):
        try:
            team = [characterTeam.members[0]] + sorted(characterTeam.members[1:])
            notexists = self.getTeamId(team) == -1
            if notexists:
                lastId = self.storage.query(func.max(DbTeam.id)).first()
                if lastId[0] is None:
                    nextId = 1
                else:
                    nextId = lastId[0] + 1
                dbTeamRecord = DbTeam(id=nextId, leader=team[0], slot2=team[1], slot3=team[2], slot4=team[3], slot5=team[4])
                self.storage.add(dbTeamRecord)
                self.storage.commit()
                return True
            else:
                return False
        except Exception as ex:
            logging.error(f'error: addCharacterTeamRecord: {ex}')
            return False

    def getTeamId(self, team):
        teamRecord = self.storage.query(DbTeam).filter_by(
            leader=team[0],
            slot2=team[1],
            slot3=team[2],
            slot4=team[3],
            slot5=team[4]
        ).first()
        if teamRecord is not None:
            return teamRecord.id
        else:
            return -1

    def addCounterTeamForRecord(self, team: CharacterTeam, teamRecord: CharacterTeamRecord):
        try:
            sortedTeam = [team.members[0]] + sorted(team.members[1:])
            sortedRecordTeam = [teamRecord.team.members[0]] + sorted(teamRecord.team.members[1:])
            recordTeamId = self.getTeamId(sortedRecordTeam)
            teamId = self.getTeamId(sortedTeam)
            if teamId == -1:
                self.addCharacterTeam(CharacterTeam(sortedTeam))
                teamId = self.getTeamId(sortedTeam)

            counterTeamExists = self.storage.query(DbTeamCounters).filter_by(
                targetteamid=recordTeamId,
                counterteamid=teamId
            ).first() is not None
            if counterTeamExists == False:
                lastCounterId = self.storage.query(func.max(DbTeamCounters.id)).first()
                if lastCounterId[0] is None:
                    nextCounterId = 1
                else:
                    nextCounterId = lastCounterId[0] + 1
                dbTeamCountersRecord = DbTeamCounters(id=nextCounterId, targetteamid=recordTeamId, counterteamid=teamId)
                self.storage.add(dbTeamCountersRecord)
                self.storage.commit()
                return True
            else:
                return False
        except Exception as ex:
            logging.error(f'error: addCounterTeamForRecord: {ex}')
            return False

    def deleteCounterTeamForRecord(self, team: CharacterTeam, teamRecord: CharacterTeamRecord):
        try:
            sortedTeam = [team.members[0]] + sorted(team.members[1:])
            recordTeamId = self.getTeamId(teamRecord.team.members)
            teamId = self.getTeamId(sortedTeam)
            self.storage.query(DbTeamCounters).filter_by(
                targetteamid=recordTeamId,
                counterteamid=teamId
            ).delete()
            self.storage.commit()
            return True
        except Exception as ex:
            logging.error(f'error: addCharacterTeamRecord: {ex}')
            return False

    def getCharacterTeamRecords(self):
        try:
            teams = self.storage.query(DbTeam.id, DbTeam.leader, DbTeam.slot2, DbTeam.slot3, DbTeam.slot4, DbTeam.slot5).all()
            return list(map(self.characterTeamRecordForTeam, teams))
        except Exception as ex:
            logging.error(f'error in retrieving characters: {ex}')
            return []

    def characterTeamRecordForTeam(self, team):
        sqlStatement = 'select leader, slot2, slot3, slot4, slot5 from teams left join ' \
                       '(select counter_teams.counterteamid from teams left join ' \
                       'counter_teams on teams.id = counter_teams.targetteamid ' \
                       f'where counter_teams.targetteamid = {team[0]}) AS res ON teams.id = res.counterteamid ' \
                       'where teams.id=res.counterteamid'
        counterTeams = self.storage.execute(text(sqlStatement)).all()
        counterCharTeams = list(map(lambda x: CharacterTeam(x), counterTeams))
        return CharacterTeamRecord(CharacterTeam(team[1:]), counterCharTeams)

    def getStorageEntity(self):
        try:
            chars = self.getAllCharacters()
            teamRecords = self.getCharacterTeamRecords()
            return StorageEntity(chars, teamRecords)
        except Exception as ex:
            logging.error(f'error in retrieving storage entity: {ex}')
            return StorageEntity([])

    def updateStorageEntity(self, entity: StorageEntity):
        try:
            teamRecords = self.getCharacterTeamRecords()
            return StorageEntity(entity.characters, teamRecords)
        except Exception as ex:
            logging.error(f'error in retrieving storage entity: {ex}')
            return entity
