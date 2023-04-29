from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from chars import Character
import logging

# Declare Mapping
Base = declarative_base()
logging.basicConfig(level=logging.INFO)

class DbChar(Base):
    __tablename__ = "chars"
    charname = Column(String, primary_key=True, nullable=False)

class DbKeyword(Base):
    __tablename__ = "char_keywords"
    keyword = Column(String, primary_key=True, nullable=False)
    charname = Column(String, ForeignKey("chars.charname"), nullable=False)

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
