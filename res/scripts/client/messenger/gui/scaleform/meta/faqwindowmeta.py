from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class FAQWindowMeta(DAAPIModule):

    def as_appendTextS(self, text):
        if self._isDAAPIInited():
            return self.flashObject.as_appendText(text)
