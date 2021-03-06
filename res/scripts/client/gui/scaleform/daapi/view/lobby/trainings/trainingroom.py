# 2013.11.15 11:26:21 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/trainings/TrainingRoom.py
import ArenaType
from adisp import process
from gui import SystemMessages
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.trainings import formatters
from gui.Scaleform.framework import AppRef, VIEW_TYPE, g_entitiesFactories
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.prb_control import context
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.view.meta.TrainingRoomMeta import TrainingRoomMeta
from gui.prb_control.prb_helpers import PrbListener
from gui.prb_control.info import getPlayersComparator
from gui.prb_control.settings import PREBATTLE_ROSTER, PREBATTLE_SETTING_NAME
from gui.prb_control.settings import REQUEST_TYPE, GUI_EXIT
from gui.shared import events, EVENT_BUS_SCOPE
from helpers import int2roman, i18n
from messenger.ext import passCensor
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from prebattle_shared import decodeRoster

class TrainingRoom(LobbySubView, TrainingRoomMeta, AppRef, PrbListener):

    @storage_getter('users')
    def usersStorage(self):
        return None

    def _populate(self):
        super(TrainingRoom, self)._populate()
        functional = self.prbFunctional
        self.__showSettings(functional)
        self.__showRosters(functional, functional.getRosters())
        self.__swapTeamsInMinimap(functional.getPlayerTeam())
        self.startPrbListening()
        self.addListener(events.CoolDownEvent.PREBATTLE, self.__handleSetPrebattleCoolDown, scope=EVENT_BUS_SCOPE.LOBBY)
        g_messengerEvents.users.onUserRosterChanged += self.__me_onUserRosterChanged

    def _dispose(self):
        super(TrainingRoom, self)._dispose()
        self.stopPrbListening()
        self.removeListener(events.CoolDownEvent.PREBATTLE, self.__handleSetPrebattleCoolDown, scope=EVENT_BUS_SCOPE.LOBBY)
        g_messengerEvents.users.onUserRosterChanged -= self.__me_onUserRosterChanged

    def onEscape(self):
        dialogsContainer = self.app.containerManager.getContainer(VIEW_TYPE.DIALOG)
        if not dialogsContainer.getView(criteria={POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.LOBBY_MENU}):
            self.fireEvent(events.ShowViewEvent(events.ShowViewEvent.SHOW_LOBBY_MENU), scope=EVENT_BUS_SCOPE.LOBBY)

    def showTrainingSettings(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_TRAINING_SETTINGS_WINDOW, ctx={'settings': context.TrainingSettingsCtx.fetch(self.prbFunctional.getSettings())}))

    def showPrebattleInvitationsForm(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_SEND_INVITES_WINDOW, {'prbName': 'training'}), scope=EVENT_BUS_SCOPE.LOBBY)

    def startTraining(self):
        self.__closeWindows()
        self.__doStartTraining()

    @process
    def __doStartTraining(self):
        result = yield self.prbDispatcher.sendPrbRequest(context.SetTeamStateCtx(1, True))
        if result:
            result = yield self.prbDispatcher.sendPrbRequest(context.SetTeamStateCtx(2, True))
            if not result:
                yield self.prbDispatcher.sendPrbRequest(context.SetTeamStateCtx(1, False))
        if not result:
            self.__showActionErrorMessage()
            self.as_disableControlsS(False)
            self.__updateStartButton(self.prbFunctional)

    def onTeamStatesReceived(self, functional, team1State, team2State):
        team, assigned = decodeRoster(functional.getRosterKey())
        if team1State.isInQueue() and team2State.isInQueue() and assigned:
            self.as_disableControlsS(True)
        elif assigned is False:
            self.as_enabledCloseButtonS(False)

    @process
    def closeTrainingRoom(self):
        result = yield self.prbDispatcher.leave(context.LeavePrbCtx(waitingID='prebattle/leave', guiExit=GUI_EXIT.TRAINING_LIST))
        if not result:
            self.__showActionErrorMessage()

    def __showActionErrorMessage(self):
        SystemMessages.pushMessage(i18n.makeString(SYSTEM_MESSAGES.TRAINING_ERROR_DOACTION), type=SystemMessages.SM_TYPE.Error)

    @process
    def changeTeam(self, accID, slot):
        roster = int(slot)
        settings = self.prbFunctional.getSettings()
        if not slot:
            roster = settings[PREBATTLE_SETTING_NAME.DEFAULT_ROSTER]
            if not roster & PREBATTLE_ROSTER.UNASSIGNED:
                roster |= PREBATTLE_ROSTER.UNASSIGNED
        result = yield self.prbDispatcher.sendPrbRequest(context.AssignPrbCtx(accID, roster, waitingID='prebattle/assign'))
        if not result:
            self.__showActionErrorMessage()

    @process
    def swapTeams(self):
        result = yield self.prbDispatcher.sendPrbRequest(context.SwapTeamsCtx(waitingID='prebattle/swap'))

    @process
    def selectCommonVoiceChat(self, index):
        result = yield self.prbDispatcher.sendPrbRequest(context.ChangeArenaVoipCtx(index, waitingID='prebattle/change_arena_voip'))

    def __closeWindows(self):
        container = self.app.containerManager.getContainer(VIEW_TYPE.WINDOW)
        if container is not None:
            for viewAlias in [VIEW_ALIAS.TRAINING_SETTINGS_WINDOW, g_entitiesFactories.getAliasByEvent(events.ShowWindowEvent.SHOW_SEND_INVITES_WINDOW)]:
                window = container.getView(criteria={POP_UP_CRITERIA.VIEW_ALIAS: viewAlias})
                if window is not None:
                    window.destroy()

        return

    def onPrbFunctionalFinished(self):
        self.__closeWindows()

    def onSettingUpdated(self, functional, settingName, settingValue):
        if settingName == PREBATTLE_SETTING_NAME.ARENA_TYPE_ID:
            arenaType = ArenaType.g_cache.get(settingValue)
            self.as_updateMapS(settingValue, arenaType.maxPlayersInTeam * 2, arenaType.name, formatters.getTrainingRoomTitle(arenaType), formatters.getArenaSubTypeString(settingValue), arenaType.description)
        elif settingName == PREBATTLE_SETTING_NAME.ROUND_LENGTH:
            self.as_updateTimeoutS(formatters.getRoundLenString(settingValue))
        elif settingName == PREBATTLE_SETTING_NAME.COMMENT:
            self.as_updateCommentS(settingValue)
        elif settingName == PREBATTLE_SETTING_NAME.ARENA_VOIP_CHANNELS:
            self.as_setArenaVoipChannelsS(settingValue)
        self.__updateStartButton(functional)

    def onRostersChanged(self, functional, rosters, full):
        if PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1 in rosters:
            self.as_setTeam1S(self.__makeAccountsData(rosters[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1]))
        if PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2 in rosters:
            self.as_setTeam2S(self.__makeAccountsData(rosters[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2]))
        if PREBATTLE_ROSTER.UNASSIGNED in rosters:
            self.as_setOtherS(self.__makeAccountsData(rosters[PREBATTLE_ROSTER.UNASSIGNED]))
        self.__updateStartButton(functional)

    def onPlayerStateChanged(self, functional, roster, accountInfo):
        stateString = formatters.getPlayerStateString(accountInfo.state)
        vContourIcon = ''
        vShortName = ''
        vLevel = ''
        if accountInfo.isVehicleSpecified():
            vehicle = accountInfo.getVehicle()
            vContourIcon = vehicle.iconContour
            vShortName = vehicle.shortUserName
            vLevel = int2roman(vehicle.level)
        if roster == PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1:
            self.as_setPlayerStateInTeam1S(accountInfo.dbID, stateString, vContourIcon, vShortName, vLevel)
        elif roster == PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2:
            self.as_setPlayerStateInTeam2S(accountInfo.dbID, stateString, vContourIcon, vShortName, vLevel)
        else:
            self.as_setPlayerStateInOtherS(accountInfo.dbID, stateString, vContourIcon, vShortName, vLevel)
        self.__updateStartButton(functional)

    def onPlayerTeamNumberChanged(self, functional, team):
        if VIEW_ALIAS.MINIMAP_LOBBY in self.components:
            self.components[VIEW_ALIAS.MINIMAP_LOBBY].swapTeams(team)

    def __showSettings(self, functional):
        settings = functional.getSettings()
        if settings is None:
            return
        else:
            isCreator = functional.isCreator()
            permissions = functional.getPermissions()
            arenaTypeID = settings['arenaTypeID']
            arenaType = ArenaType.g_cache.get(arenaTypeID)
            if isCreator:
                comment = settings['comment']
            else:
                comment = passCensor(settings['comment'])
            self.as_setInfoS({'isCreator': isCreator,
             'creator': settings[PREBATTLE_SETTING_NAME.CREATOR],
             'title': formatters.getTrainingRoomTitle(arenaType),
             'arenaName': arenaType.name,
             'arenaTypeID': arenaTypeID,
             'arenaSubType': formatters.getArenaSubTypeString(arenaTypeID),
             'description': arenaType.description,
             'maxPlayersCount': arenaType.maxPlayersInTeam * 2,
             'roundLenString': formatters.getRoundLenString(settings['roundLength']),
             'comment': comment,
             'arenaVoipChannels': settings[PREBATTLE_SETTING_NAME.ARENA_VOIP_CHANNELS],
             'canChangeArenaVOIP': permissions.canChangeArenaVOIP()})
            return

    def __showRosters(self, functional, rosters):
        accounts = rosters[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1]
        if len(accounts):
            self.as_setTeam1S(self.__makeAccountsData(accounts))
        accounts = rosters[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2]
        if len(accounts):
            self.as_setTeam2S(self.__makeAccountsData(accounts))
        accounts = rosters[PREBATTLE_ROSTER.UNASSIGNED]
        if len(accounts):
            self.as_setOtherS(self.__makeAccountsData(accounts))
        self.__updateStartButton(functional)

    def __updateStartButton(self, functional):
        if functional.isCreator():
            isInRange, state = functional.getLimits().isTeamsValid()
            self.as_disableStartButtonS(not isInRange)
            if state == '' and isInRange:
                self.as_enabledCloseButtonS(True)
        else:
            self.as_disableStartButtonS(True)

    def __swapTeamsInMinimap(self, team):
        if VIEW_ALIAS.MINIMAP_LOBBY in self.components:
            self.components[VIEW_ALIAS.MINIMAP_LOBBY].swapTeams(team)

    def __makeAccountsData(self, accounts):
        result = []
        isPlayerSpeaking = self.app.voiceChatManager.isPlayerSpeaking
        accounts = sorted(accounts, cmp=getPlayersComparator())
        getUser = self.usersStorage.getUser
        for account in accounts:
            vContourIcon = ''
            vShortName = ''
            vLevel = ''
            dbID = account.dbID
            user = getUser(dbID)
            if account.isVehicleSpecified():
                vehicle = account.getVehicle()
                vContourIcon = vehicle.iconContour
                vShortName = vehicle.shortUserName
                vLevel = int2roman(vehicle.level)
            result.append({'accID': account.accID,
             'uid': account.dbID,
             'userName': account.name,
             'fullName': account.getFullName(),
             'himself': account.isCurrentPlayer(),
             'stateString': formatters.getPlayerStateString(account.state),
             'icon': vContourIcon,
             'vShortName': vShortName,
             'vLevel': vLevel,
             'chatRoster': user.getRoster() if user else 0,
             'isPlayerSpeaking': bool(isPlayerSpeaking(account.dbID))})

        return result

    def __handleSetPrebattleCoolDown(self, event):
        if event.requestID is REQUEST_TYPE.CHANGE_SETTINGS:
            self.as_startCoolDownSettingS(event.coolDown)
        elif event.requestID is REQUEST_TYPE.SWAP_TEAMS:
            self.as_startCoolDownSwapButtonS(event.coolDown)
        elif event.requestID is REQUEST_TYPE.CHANGE_ARENA_VOIP:
            self.as_startCoolDownVoiceChatS(event.coolDown)

    def __me_onUserRosterChanged(self, _, user):
        dbID = user.getID()
        playerInfo = self.prbFunctional.getPlayerInfoByDbID(dbID)
        if playerInfo is None:
            return
        else:
            roster = playerInfo.roster
            if roster == PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1:
                self.as_setPlayerChatRosterInTeam1S(dbID, user.getRoster())
            elif roster == PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2:
                self.as_setPlayerChatRosterInTeam2S(dbID, user.getRoster())
            else:
                self.as_setPlayerChatRosterInOtherS(dbID, user.getRoster())
            return
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/trainings/trainingroom.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:21 EST
