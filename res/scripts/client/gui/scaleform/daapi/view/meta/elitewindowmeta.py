# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/EliteWindowMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class EliteWindowMeta(DAAPIModule):

    def as_setVehTypeCompDescrS(self, typeCompDescr):
        if self._isDAAPIInited():
            return self.flashObject.as_setVehTypeCompDescr(typeCompDescr)