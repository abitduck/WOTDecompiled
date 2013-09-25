# Embedded file name: scripts/client/gui/prb_control/functional/__init__.py
from constants import PREBATTLE_TYPE, IS_DEVELOPMENT
from debug_utils import LOG_ERROR
from gui import prb_control
from gui.prb_control.functional.company import CompanyEntry, CompanyFunctional
from gui.prb_control.functional.default import PrbInitFunctional
from gui.prb_control.functional.no_prebattle import NoPrbFunctional
from gui.prb_control.functional.not_supported import NotSupportedEntry
from gui.prb_control.functional.not_supported import PrbNotSupportedFunctional
from gui.prb_control.functional.queues import LeaveRandomFunctional
from gui.prb_control.functional.queues import JoinRandomFunctional
from gui.prb_control.functional.squad import SquadEntry, SquadFunctional
from gui.prb_control.functional.training import TrainingEntry, TrainingFunctional
from gui.prb_control.functional.battle_session import BattleSessionEntry, BattleSessionFunctional
_SUPPORTED_PREBATTLE = {PREBATTLE_TYPE.TRAINING: (TrainingEntry, TrainingFunctional),
 PREBATTLE_TYPE.SQUAD: (SquadEntry, SquadFunctional),
 PREBATTLE_TYPE.COMPANY: (CompanyEntry, CompanyFunctional),
 PREBATTLE_TYPE.TOURNAMENT: (BattleSessionEntry, BattleSessionFunctional),
 PREBATTLE_TYPE.CLAN: (BattleSessionEntry, BattleSessionFunctional)}

def addPrbToSupport(prbType, entryClass, funcClass):
    global _SUPPORTED_PREBATTLE
    _SUPPORTED_PREBATTLE[prbType] = (entryClass, funcClass)


def createPrbEntry(prbType):
    if prbType in _SUPPORTED_PREBATTLE:
        prbEntry = _SUPPORTED_PREBATTLE[prbType][0]()
    else:
        LOG_ERROR('Given type of prebattle is not supported', prbType)
        prbEntry = NotSupportedEntry()
    return prbEntry


def createPrbFunctional(dispatcher):
    clientPrb = prb_control.getClientPrebattle()
    if clientPrb is not None:
        if prb_control.isPrebattleSettingsReceived(prebattle=clientPrb):
            prbSettings = prb_control.getPrebattleSettings(prebattle=clientPrb)
            prbType = prb_control.getPrebattleType(settings=prbSettings)
            if prbType in _SUPPORTED_PREBATTLE:
                prbFunctional = _SUPPORTED_PREBATTLE[prbType][1](prbSettings)
                for listener in dispatcher._globalListeners:
                    prbFunctional.addListener(listener())

            else:
                LOG_ERROR('Prebattle with given type is not supported', prbType)
                prbFunctional = PrbNotSupportedFunctional(prbSettings)
        else:
            prbFunctional = PrbInitFunctional(dispatcher)
    else:
        prbFunctional = NoPrbFunctional()
    return prbFunctional


def createQueueFunctional(isInRandomQueue = False):
    if isInRandomQueue:
        functional = LeaveRandomFunctional()
    else:
        functional = JoinRandomFunctional()
    return functional


def initDevFunctional():
    if IS_DEVELOPMENT:
        try:
            from gui.prb_control.functional.dev import init
        except ImportError:
            init = lambda : None

        init()


def finiDevFunctional():
    if IS_DEVELOPMENT:
        try:
            from gui.prb_control.functional.dev import fini
        except ImportError:
            fini = lambda : None

        fini()