# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/VehicleSelector.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class VehicleSelector(DAAPIModule):

    def as_setDataS(self, stub):
        if self._isDAAPIInited():
            return self.flashObject.as_setData(stub)