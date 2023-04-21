import cv2
from chars import CharProvider

class ImageGenerator:

    def createImage(charName):
        char = CharProvider.charByKey(charName)
        return cv2.imread(char.path)

    def generateTeamImage(charsList, username, sendToChat = False):
        images = list(map(ImageGenerator.createImage, charsList))
        team = cv2.hconcat(images)
        if sendToChat:
            cv2.imwrite(f'result/res-{username}.png', team)
            res = open(f'result/res-{username}.png', 'rb')
            return res
        else:
            return team

    def generateImageForCharacterTeamRecord(characterTeamRecord, username):
        targetTitle = cv2.imread('images/rows/target.png')
        counterTitle = cv2.imread('images/rows/counter.png')

        team = ImageGenerator.generateTeamImage(characterTeamRecord.team.members, username)

        counters = []
        for counterTeam in characterTeamRecord.counterTeams:
            counters.append(ImageGenerator.generateTeamImage(counterTeam.members, username))

        img = cv2.vconcat([targetTitle, team, counterTitle] + counters)
        cv2.imwrite(f'result/res-{username}.png', img)
        res = open(f'result/res-{username}.png', 'rb')
        return res

ImageGenerator.createImage = staticmethod(ImageGenerator.createImage)
ImageGenerator.generateTeamImage = staticmethod(ImageGenerator.generateTeamImage)
ImageGenerator.generateImageForCharacterTeamRecord = staticmethod(ImageGenerator.generateImageForCharacterTeamRecord)