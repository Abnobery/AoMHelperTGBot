import cv2

class ImageGenerator:

    @staticmethod
    def createImage(character):
        return cv2.imread(character.path)

    @staticmethod
    def generateTeamImage(charsList, username, sendToChat = False):
        images = list(map(ImageGenerator.createImage, charsList))
        team = cv2.hconcat(images)
        if sendToChat:
            cv2.imwrite(f'result/res-{username}.png', team)
            res = open(f'result/res-{username}.png', 'rb')
            return res
        else:
            return team

    @staticmethod
    def generateImageForCharacterTeamRecord(storageEntity, characterTeamRecord, username):
        targetTitle = cv2.imread('images/rows/target.png')
        counterTitle = cv2.imread('images/rows/counter.png')
        teamCharList = storageEntity.charsFromKeys(characterTeamRecord.team.members)

        team = ImageGenerator.generateTeamImage(teamCharList, username)

        counters = []
        for counterTeam in characterTeamRecord.counterTeams:
            counterCharList = storageEntity.charsFromKeys(counterTeam.members)
            counters.append(ImageGenerator.generateTeamImage(counterCharList, username))

        img = cv2.vconcat([targetTitle, team, counterTitle] + counters)
        cv2.imwrite(f'result/res-{username}.png', img)
        res = open(f'result/res-{username}.png', 'rb')
        return res

    @staticmethod
    def generateEffectiveTeamsImageForCharacterTeamRecord(storageEntity, characterTeamRecord, effectiveTeams, username):
        effectiveTitle = cv2.imread('images/rows/effective.png')
        teamCharList = storageEntity.charsFromKeys(characterTeamRecord.team.members)

        team = ImageGenerator.generateTeamImage(teamCharList, username)
        effTeams = []
        for effectiveTeam in effectiveTeams[:10]:
            teamCharList = storageEntity.charsFromKeys(effectiveTeam.members)
            effTeams.append(ImageGenerator.generateTeamImage(teamCharList, username))

        img = cv2.vconcat([team, effectiveTitle] + effTeams)
        cv2.imwrite(f'result/res_eff-{username}.png', img)
        res = open(f'result/res_eff-{username}.png', 'rb')
        return res