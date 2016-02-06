#!/usr/bin/env python
#--!-- coding: utf8 --!--

from qt import *

from ui.settings import *
from enums import *
from functions import *
from ui.editors.themes import *
from ui.views.textEditView import *
import settings
import os

# Spell checker support
try:
    import enchant
except ImportError:
    enchant = None

class settingsWindow(QWidget, Ui_Settings):
    
    def __init__(self, mainWindow):
        QWidget.__init__(self)
        self.setupUi(self)
        self.mw = mainWindow
        
        # UI
        for i in range(self.lstMenu.count()):
            item = self.lstMenu.item(i)
            item.setSizeHint(QSize(item.sizeHint().width(), 42))
            item.setTextAlignment(Qt.AlignCenter)
        self.lstMenu.setMaximumWidth(150)
        
        # General
        self.cmbStyle.addItems(list(QStyleFactory.keys()))
        self.cmbStyle.setCurrentIndex([i.lower() for i in list(QStyleFactory.keys())].index(qApp.style().objectName()))
        self.cmbStyle.currentIndexChanged[str].connect(self.setStyle)
        
        self.txtAutoSave.setValidator(QIntValidator(0, 999, self))
        self.txtAutoSaveNoChanges.setValidator(QIntValidator(0, 999, self))
        self.chkAutoSave.setChecked(settings.autoSave)
        self.chkAutoSaveNoChanges.setChecked(settings.autoSaveNoChanges)
        self.txtAutoSave.setText(str(settings.autoSaveDelay))
        self.txtAutoSaveNoChanges.setText(str(settings.autoSaveNoChangesDelay))
        self.chkSaveOnQuit.setChecked(settings.saveOnQuit)
        self.chkAutoSave.stateChanged.connect(self.saveSettingsChanged)
        self.chkAutoSaveNoChanges.stateChanged.connect(self.saveSettingsChanged)
        self.chkSaveOnQuit.stateChanged.connect(self.saveSettingsChanged)
        self.txtAutoSave.textEdited.connect(self.saveSettingsChanged)
        self.txtAutoSaveNoChanges.textEdited.connect(self.saveSettingsChanged)
        autoLoad, last = self.mw.welcome.getAutoLoadValues()
        self.chkAutoLoad.setChecked(autoLoad)
        self.chkAutoLoad.stateChanged.connect(self.saveSettingsChanged)
        
        dtt = [
            ("t2t", self.tr("Txt2Tags"), "text-x-script"),
            ("html", self.tr("Rich Text (html)"), "text-html"),
            ("txt", self.tr("Plain Text"), "text-x-generic"),
            ]
        self.cmbDefaultTextType.clear()
        for t in dtt:
            self.cmbDefaultTextType.addItem(QIcon.fromTheme(t[2]), t[1], t[0])
        i = self.cmbDefaultTextType.findData(settings.defaultTextType)
        if i != -1:
            self.cmbDefaultTextType.setCurrentIndex(i)
        self.cmbDefaultTextType.currentIndexChanged.connect(self.saveSettingsChanged)
        
        # Revisions
        opt = settings.revisions
        self.chkRevisionsKeep.setChecked(opt["keep"])
        self.chkRevisionsKeep.stateChanged.connect(self.revisionsSettingsChanged)
        self.chkRevisionRemove.setChecked(opt["smartremove"])
        self.chkRevisionRemove.toggled.connect(self.revisionsSettingsChanged)
        self.spnRevisions10Mn.setValue(60 / opt["rules"][10 * 60])
        self.spnRevisions10Mn.valueChanged.connect(self.revisionsSettingsChanged)
        self.spnRevisionsHour.setValue(60 * 10 / opt["rules"][60 * 60])
        self.spnRevisionsHour.valueChanged.connect(self.revisionsSettingsChanged)
        self.spnRevisionsDay.setValue(60 * 60 / opt["rules"][60 * 60 * 24])
        self.spnRevisionsDay.valueChanged.connect(self.revisionsSettingsChanged)
        self.spnRevisionsMonth.setValue(60 * 60 * 24 / opt["rules"][60 * 60 * 24 * 30])
        self.spnRevisionsMonth.valueChanged.connect(self.revisionsSettingsChanged)
        self.spnRevisionsEternity.setValue(60 * 60 * 24 * 7 / opt["rules"][None])
        self.spnRevisionsEternity.valueChanged.connect(self.revisionsSettingsChanged)
        
        # Views
        self.tabViews.setCurrentIndex(0)
        lst = ["Nothing", "POV", "Label", "Progress", "Compile"]
        for cmb in self.viewSettingsDatas():
            item, part = self.viewSettingsDatas()[cmb]
            cmb.setCurrentIndex(lst.index(settings.viewSettings[item][part]))
            cmb.currentIndexChanged.connect(self.viewSettingsChanged)
        
        for chk in self.outlineColumnsData():
            col = self.outlineColumnsData()[chk]
            chk.setChecked(col in settings.outlineViewColumns)
            chk.stateChanged.connect(self.outlineColumnsChanged)
        
        for item, what, value in [
            (self.rdoTreeItemCount, "InfoFolder", "Count"),
            (self.rdoTreeWC, "InfoFolder", "WC"),
            (self.rdoTreeProgress, "InfoFolder", "Progress"),
            (self.rdoTreeNothing, "InfoFolder", "Nothing"),
            (self.rdoTreeTextWC, "InfoText", "WC"),
            (self.rdoTreeTextProgress, "InfoText", "Progress"),
            (self.rdoTreeTextNothing, "InfoText", "Nothing"),
            ]:
            item.setChecked(settings.viewSettings["Tree"][what] == value)
            item.toggled.connect(self.treeViewSettignsChanged)
            
        self.populatesCmbBackgrounds(self.cmbCorkImage)
        self.setCorkImageDefault()
        self.updateCorkColor()
        self.cmbCorkImage.currentIndexChanged.connect(self.setCorkBackground)
        self.btnCorkColor.clicked.connect(self.setCorkColor)
        
        # Text editor
        opt = settings.textEditor
        self.setButtonColor(self.btnEditorFontColor, opt["fontColor"])
        self.btnEditorFontColor.clicked.connect(self.choseEditorFontColor)
        self.setButtonColor(self.btnEditorMisspelledColor, opt["misspelled"])
        self.btnEditorMisspelledColor.clicked.connect(self.choseEditorMisspelledColor)
        self.setButtonColor(self.btnEditorBackgroundColor, opt["background"])
        self.btnEditorBackgroundColor.clicked.connect(self.choseEditorBackgroundColor)
        f = QFont()
        f.fromString(opt["font"])
        self.cmbEditorFontFamily.setCurrentFont(f)
        self.cmbEditorFontFamily.currentFontChanged.connect(self.updateEditorSettings)
        self.spnEditorFontSize.setValue(f.pointSize())
        self.spnEditorFontSize.valueChanged.connect(self.updateEditorSettings)
        self.cmbEditorLineSpacing.setCurrentIndex(
            0 if opt["lineSpacing"] == 100 else
            1 if opt["lineSpacing"] == 150 else
            2 if opt["lineSpacing"] == 200 else
            3)
        self.cmbEditorLineSpacing.currentIndexChanged.connect(self.updateEditorSettings)
        self.spnEditorLineSpacing.setValue(opt["lineSpacing"])
        self.spnEditorLineSpacing.valueChanged.connect(self.updateEditorSettings)
        self.spnEditorLineSpacing.setEnabled(opt["lineSpacing"] not in [100, 150, 200])
        self.spnEditorLineSpacing.valueChanged.connect(self.updateEditorSettings)
        self.spnEditorTabWidth.setValue(opt["tabWidth"])
        self.spnEditorTabWidth.valueChanged.connect(self.updateEditorSettings)
        self.chkEditorIndent.setChecked(opt["indent"])
        self.chkEditorIndent.stateChanged.connect(self.updateEditorSettings)
        self.spnEditorParaAbove.setValue(opt["spacingAbove"])
        self.spnEditorParaAbove.valueChanged.connect(self.updateEditorSettings)
        self.spnEditorParaBelow.setValue(opt["spacingBelow"])
        self.spnEditorParaAbove.valueChanged.connect(self.updateEditorSettings)
        
        # Labels
        self.lstLabels.setModel(self.mw.mdlLabels)
        self.lstLabels.setRowHidden(0, True)
        self.lstLabels.clicked.connect(self.updateLabelColor)
        self.btnLabelAdd.clicked.connect(self.addLabel)
        self.btnLabelRemove.clicked.connect(self.removeLabel)
        self.btnLabelColor.clicked.connect(self.setLabelColor)
        
        # Statuses
        self.lstStatus.setModel(self.mw.mdlStatus)
        self.lstStatus.setRowHidden(0, True)
        self.btnStatusAdd.clicked.connect(self.addStatus)
        self.btnStatusRemove.clicked.connect(self.removeStatus)
        
        # Fullscreen
        self._editingTheme = None
        self.btnThemeEditOK.setIcon(qApp.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btnThemeEditOK.clicked.connect(self.saveTheme)
        self.btnThemeEditCancel.setIcon(qApp.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.btnThemeEditCancel.clicked.connect(self.cancelEdit)
        self.cmbThemeEdit.currentIndexChanged.connect(self.themeEditStack.setCurrentIndex)
        self.cmbThemeEdit.setCurrentIndex(0)
        self.cmbThemeEdit.currentIndexChanged.emit(0)
        self.themeStack.setCurrentIndex(0)
        self.lstThemes.currentItemChanged.connect(self.themeSelected)
        self.populatesThemesList()
        self.btnThemeAdd.clicked.connect(self.newTheme)
        self.btnThemeEdit.clicked.connect(self.editTheme)
        self.btnThemeRemove.clicked.connect(self.removeTheme)
        
        
    def setTab(self, tab):
        
        tabs = {
            "General":0,
            "Views":1,
            "Labels":2,
            "Status":3,
            "Fullscreen":4,
            }
        
        if tab in tabs:
            self.lstMenu.setCurrentRow(tabs[tab])
        else:
            self.lstMenu.setCurrentRow(tab)
####################################################################################################
#                                           GENERAL                                                #
####################################################################################################
        
    def setStyle(self, style):
        #Save style to Qt Settings
        sttgs = QSettings(qApp.organizationName(), qApp.applicationName())
        sttgs.setValue("applicationStyle", style)
        qApp.setStyle(style)
        
    def saveSettingsChanged(self):
        if self.txtAutoSave.text() in ["", "0"]:
            self.txtAutoSave.setText("1")
        if self.txtAutoSaveNoChanges.text() in ["", "0"]:
            self.txtAutoSaveNoChanges.setText("1")
        
        sttgs = QSettings()
        sttgs.setValue("autoLoad", True if self.chkAutoLoad.checkState() else False)
        sttgs.sync()
        
        settings.autoSave = True if self.chkAutoSave.checkState() else False
        settings.autoSaveNoChanges = True if self.chkAutoSaveNoChanges.checkState() else False
        settings.saveOnQuit = True if self.chkSaveOnQuit.checkState() else False
        settings.autoSaveDelay = int(self.txtAutoSave.text())
        settings.autoSaveNoChangesDelay = int(self.txtAutoSaveNoChanges.text())
        self.mw.saveTimer.setInterval(settings.autoSaveDelay * 60 * 1000)
        self.mw.saveTimerNoChanges.setInterval(settings.autoSaveNoChangesDelay * 1000)
        settings.defaultTextType = self.cmbDefaultTextType.currentData()


####################################################################################################
#                                           REVISION                                               #
####################################################################################################

    def revisionsSettingsChanged(self):
        opt = settings.revisions
        opt["keep"] = True if self.chkRevisionsKeep.checkState() else False
        opt["smartremove"] = self.chkRevisionRemove.isChecked()
        opt["rules"][10 * 60] = 60 / self.spnRevisions10Mn.value()
        opt["rules"][60 * 60] = 60 * 10 / self.spnRevisionsHour.value()
        opt["rules"][60 * 60 * 24] = 60 * 60 / self.spnRevisionsDay.value()
        opt["rules"][60 * 60 * 24 * 30] = 60 * 60 * 24 / self.spnRevisionsMonth.value()
        opt["rules"][None] = 60 * 60 * 24 * 7 / self.spnRevisionsEternity.value()
        
####################################################################################################
#                                           VIEWS                                                  #
####################################################################################################

    def viewSettingsDatas(self):
        return {
            self.cmbTreeIcon: ("Tree", "Icon"),
            self.cmbTreeText: ("Tree", "Text"),
            self.cmbTreeBackground: ("Tree", "Background"),
            self.cmbOutlineIcon: ("Outline", "Icon"),
            self.cmbOutlineText: ("Outline", "Text"),
            self.cmbOutlineBackground: ("Outline", "Background"),
            self.cmbCorkIcon: ("Cork", "Icon"),
            self.cmbCorkText: ("Cork", "Text"),
            self.cmbCorkBackground: ("Cork", "Background"),
            self.cmbCorkBorder: ("Cork", "Border"),
            self.cmbCorkCorner: ("Cork", "Corner")
            }
        
    def viewSettingsChanged(self):
        cmb = self.sender()
        lst = ["Nothing", "POV", "Label", "Progress", "Compile"]
        item, part = self.viewSettingsDatas()[cmb]
        element = lst[cmb.currentIndex()]
        self.mw.setViewSettings(item, part, element)
        
    def outlineColumnsData(self):
        return {
            self.chkOutlineTitle: Outline.title.value,
            self.chkOutlinePOV: Outline.POV.value,
            self.chkOutlineLabel: Outline.label.value,
            self.chkOutlineStatus: Outline.status.value,
            self.chkOutlineCompile: Outline.compile.value,
            self.chkOutlineWordCount: Outline.wordCount.value,
            self.chkOutlineGoal: Outline.goal.value,
            self.chkOutlinePercentage: Outline.goalPercentage.value,
            }
        
    def outlineColumnsChanged(self):
        chk = self.sender()
        val = True if chk.checkState() else False
        col = self.outlineColumnsData()[chk]
        if val and not col in settings.outlineViewColumns:
            settings.outlineViewColumns.append(col)
        elif not val and col in settings.outlineViewColumns:
            settings.outlineViewColumns.remove(col)
        
        # Update views
        self.mw.redacEditor.outlineView.hideColumns()
        self.mw.treePlanOutline.hideColumns()
        
    def treeViewSettignsChanged(self):
        for item, what, value in [
            (self.rdoTreeItemCount, "InfoFolder", "Count"),
            (self.rdoTreeWC, "InfoFolder", "WC"),
            (self.rdoTreeProgress, "InfoFolder", "Progress"),
            (self.rdoTreeNothing, "InfoFolder", "Nothing"),
            (self.rdoTreeTextWC, "InfoText", "WC"),
            (self.rdoTreeTextProgress, "InfoText", "Progress"),
            (self.rdoTreeTextNothing, "InfoText", "Nothing"),
            ]:
            if item.isChecked():
                settings.viewSettings["Tree"][what] = value
                
        self.mw.treeRedacOutline.viewport().update()
        
    def setCorkColor(self):
        color = QColor(settings.corkBackground["color"])
        self.colorDialog = QColorDialog(color, self)
        color = self.colorDialog.getColor(color)
        if color.isValid():
            settings.corkBackground["color"] = color.name()
            self.updateCorkColor()
            # Update Cork view 
            self.mw.mainEditor.updateCorkBackground()
        
    def updateCorkColor(self):
        self.btnCorkColor.setStyleSheet("background:{};".format(settings.corkBackground["color"]))
    
    def setCorkBackground(self, i):
        img = self.cmbCorkImage.itemData(i)
        if img:
            settings.corkBackground["image"] = img
        else:
            settings.corkBackground["image"] = ""
        # Update Cork view 
        self.mw.mainEditor.updateCorkBackground()
    
    def populatesCmbBackgrounds(self, cmb):
        #self.cmbDelegate = cmbPixmapDelegate()
        #self.cmbCorkImage.setItemDelegate(self.cmbDelegate)
        
        paths = allPaths("resources/backgrounds")
        cmb.clear()
        cmb.addItem(QIcon.fromTheme("list-remove"), "", "")
        for p in paths:
            lst = os.listdir(p)
            for l in lst:
                if l.lower()[-4:] in [".jpg", ".png"] or \
                l.lower()[-5:] in [".jpeg"]:
                    px = QPixmap(os.path.join(p, l)).scaled(128, 64, Qt.KeepAspectRatio)
                    cmb.addItem(QIcon(px), "", os.path.join(p, l))
        
        cmb.setIconSize(QSize(128, 64))
        
    def setCorkImageDefault(self):
        if settings.corkBackground["image"] != "":
            i = self.cmbCorkImage.findData(settings.corkBackground["image"])
            if i != -1:
                self.cmbCorkImage.setCurrentIndex(i)

####################################################################################################
# VIEWS / EDITOR
####################################################################################################

    def updateEditorSettings(self):
        # Store settings
        f = self.cmbEditorFontFamily.currentFont()
        f.setPointSize(self.spnEditorFontSize.value())
        settings.textEditor["font"] = f.toString()
        settings.textEditor["lineSpacing"] = \
            100 if self.cmbEditorLineSpacing.currentIndex() == 0 else\
            150 if self.cmbEditorLineSpacing.currentIndex() == 1 else\
            200 if self.cmbEditorLineSpacing.currentIndex() == 2 else\
            self.spnEditorLineSpacing.value()
        self.spnEditorLineSpacing.setEnabled(self.cmbEditorLineSpacing.currentIndex() == 3)
        settings.textEditor["tabWidth"] = self.spnEditorTabWidth.value()
        settings.textEditor["indent"] = True if self.chkEditorIndent.checkState() else False
        settings.textEditor["spacingAbove"] = self.spnEditorParaAbove.value()
        settings.textEditor["spacingBelow"] = self.spnEditorParaBelow.value()
        
        # Update font and defaultBlockFormat to all textEditView. Drastically.
        for w in mainWindow().findChildren(textEditView, QRegExp(".*")):
            w.loadFontSettings()
        
    def choseEditorFontColor(self):
        color = settings.textEditor["fontColor"]
        self.colorDialog = QColorDialog(QColor(color), self)
        color = self.colorDialog.getColor(QColor(color))
        if color.isValid():
            settings.textEditor["fontColor"] = color.name()
            self.setButtonColor(self.btnEditorFontColor, color.name())
            self.updateEditorSettings()

    def choseEditorMisspelledColor(self):
        color = settings.textEditor["misspelled"]
        self.colorDialog = QColorDialog(QColor(color), self)
        color = self.colorDialog.getColor(QColor(color))
        if color.isValid():
            settings.textEditor["misspelled"] = color.name()
            self.setButtonColor(self.btnEditorMisspelledColor, color.name())
            self.updateEditorSettings()
            
    def choseEditorBackgroundColor(self):
        color = settings.textEditor["background"]
        self.colorDialog = QColorDialog(QColor(color), self)
        color = self.colorDialog.getColor(QColor(color))
        if color.isValid():
            settings.textEditor["background"] = color.name()
            self.setButtonColor(self.btnEditorBackgroundColor, color.name())
            self.updateEditorSettings()
            
    

####################################################################################################
#                                           STATUS                                                 #
####################################################################################################

    def addStatus(self):
        self.mw.mdlStatus.appendRow(QStandardItem(self.tr("New status")))
        
    def removeStatus(self):
        for i in self.lstStatus.selectedIndexes():
            self.mw.mdlStatus.removeRows(i.row(), 1)
    
####################################################################################################
#                                           LABELS                                                 #
####################################################################################################
        
    def updateLabelColor(self, index):
        #px = QPixmap(64, 64)
        #px.fill(iconColor(self.mw.mdlLabels.item(index.row()).icon()))
        #self.btnLabelColor.setIcon(QIcon(px))
        self.btnLabelColor.setStyleSheet("background:{};".format(iconColor(self.mw.mdlLabels.item(index.row()).icon()).name()))
        self.btnLabelColor.setEnabled(True)
    
    def addLabel(self):
        px = QPixmap(32, 32)
        px.fill(Qt.transparent)
        self.mw.mdlLabels.appendRow(QStandardItem(QIcon(px), self.tr("New label")))
    
    def removeLabel(self):
        for i in self.lstLabels.selectedIndexes():
            self.mw.mdlLabels.removeRows(i.row(), 1)
            
    def setLabelColor(self):
        index = self.lstLabels.currentIndex()
        color = iconColor(self.mw.mdlLabels.item(index.row()).icon())
        self.colorDialog = QColorDialog(color, self)
        color = self.colorDialog.getColor(color)
        if color.isValid():
            px = QPixmap(32, 32)
            px.fill(color)
            self.mw.mdlLabels.item(index.row()).setIcon(QIcon(px))
            self.updateLabelColor(index)
    
####################################################################################################
#                                       FULLSCREEN                                                 #
####################################################################################################

    def themeSelected(self, current, previous):
        if current:
            # UI updates
            self.btnThemeEdit.setEnabled(current.data(Qt.UserRole+1))
            self.btnThemeRemove.setEnabled(current.data(Qt.UserRole+1))
            # Save settings
            theme = current.data(Qt.UserRole)
            settings.fullScreenTheme = os.path.splitext(os.path.split(theme)[1])[0]
        else:
            # UI updates
            self.btnThemeEdit.setEnabled(False)
            self.btnThemeRemove.setEnabled(False)
    
    def newTheme(self):
        path = writablePath("resources/themes")
        name = self.tr("newtheme")
        if os.path.exists(os.path.join(path, "{}.theme".format(name))):
            i = 1
            while os.path.exists(os.path.join(path, "{}_{}.theme".format(name, i))):
                i += 1
            name = os.path.join(path, "{}_{}.theme".format(name, i))
        else:
            name = os.path.join(path, "{}.theme".format(name))
        
        settings = QSettings(name, QSettings.IniFormat)
        settings.setValue("Name", self.tr("New theme"))
        settings.sync()
        
        self.populatesThemesList()
        
    def editTheme(self):
        item = self.lstThemes.currentItem()
        theme = item.data(Qt.UserRole)
        self.loadTheme(theme)
        self.themeStack.setCurrentIndex(1)
    
    def removeTheme(self):
        item = self.lstThemes.currentItem()
        theme = item.data(Qt.UserRole)
        os.remove(theme)
        self.populatesThemesList()
    
    def populatesThemesList(self):
        paths = allPaths("resources/themes")
        current = settings.fullScreenTheme
        self.lstThemes.clear()
        
        for p in paths:
            lst = [i for i in os.listdir(p) if os.path.splitext(i)[1] == ".theme"]
            for t in lst:
                theme = os.path.join(p, t)
                editable = not appPath() in theme
                n = getThemeName(theme)
                
                item = QListWidgetItem(n)
                item.setData(Qt.UserRole, theme)
                item.setData(Qt.UserRole+1, editable)
                
                thumb = os.path.join(p, t.replace(".theme", ".jpg"))
                px = QPixmap(200, 120)
                px.fill(Qt.white)
                if not os.path.exists(thumb):
                    currentScreen = qApp.desktop().screenNumber(self)
                    screenRect = qApp.desktop().screenGeometry(currentScreen)
                    thumb = createThemePreview(theme, screenRect)
                    
                icon = QPixmap(thumb).scaled(200, 120, Qt.KeepAspectRatio)
                painter = QPainter(px)
                painter.drawPixmap(px.rect().center()-icon.rect().center(), icon)
                painter.end()
                item.setIcon(QIcon(px))
                
                self.lstThemes.addItem(item)
                
                if current and current in t:
                    self.lstThemes.setCurrentItem(item)
                    current = None
                
        self.lstThemes.setIconSize(QSize(200, 120))
        
        if current:  # the theme from settings wasn't found
                     # select the last from the list
            self.lstThemes.setCurrentRow(self.lstThemes.count() - 1)
        
    def loadTheme(self, theme):
        self._editingTheme = theme
        self._loadingTheme = True  # So we don't generate preview while loading
        
        # Load datas
        self._themeData = loadThemeDatas(theme)
        
        # Window Background
        self.btnThemWindowBackgroundColor.clicked.connect(lambda: self.getThemeColor("Background/Color"))
        try:
            self.cmbThemeBackgroundImage.disconnect()
        except:
            pass
        self.populatesCmbBackgrounds(self.cmbThemeBackgroundImage)
        self.cmbThemeBackgroundImage.currentIndexChanged.connect(self.updateThemeBackground)
        self.cmbThemBackgroundType.currentIndexChanged.connect(lambda i: self.setSetting("Background/Type", i))
        
        # Text Background
        self.btnThemeTextBackgroundColor.clicked.connect(lambda: self.getThemeColor("Foreground/Color"))
        self.spnThemeTextBackgroundOpacity.valueChanged.connect(lambda v: self.setSetting("Foreground/Opacity", v))
        self.spnThemeTextMargins.valueChanged.connect(lambda v: self.setSetting("Foreground/Margin", v))
        self.spnThemeTextPadding.valueChanged.connect(lambda v: self.setSetting("Foreground/Padding", v))
        self.cmbThemeTextPosition.currentIndexChanged.connect(lambda i: self.setSetting("Foreground/Position", i))
        self.spnThemeTextRadius.valueChanged.connect(lambda v: self.setSetting("Foreground/Rounding", v))
        self.spnThemeTextWidth.valueChanged.connect(lambda v: self.setSetting("Foreground/Width", v))
        
        # Text Options
        self.btnThemeTextColor.clicked.connect(lambda: self.getThemeColor("Text/Color"))
        self.cmbThemeFont.currentFontChanged.connect(self.updateThemeFont)
        try:
            self.cmbThemeFontSize.currentIndexChanged.disconnect(self.updateThemeFont)
        except:
            pass
        self.populatesFontSize()
        self.cmbThemeFontSize.currentIndexChanged.connect(self.updateThemeFont)
        self.btnThemeMisspelledColor.clicked.connect(lambda: self.getThemeColor("Text/Misspelled"))
        
        # Paragraph Options
        self.chkThemeIndent.stateChanged.connect(lambda v: self.setSetting("Spacings/IndendFirstLine", v!=0))
        self.cmbThemeLineSpacing.currentIndexChanged.connect(self.updateLineSpacing)
        self.cmbThemeLineSpacing.currentIndexChanged.connect(self.updateLineSpacing)
        self.spnThemeLineSpacing.valueChanged.connect(lambda v: self.setSetting("Spacings/LineSpacing", v))
        self.spnThemeParaAbove.valueChanged.connect(lambda v: self.setSetting("Spacings/ParagraphAbove", v))
        self.spnThemeParaBelow.valueChanged.connect(lambda v: self.setSetting("Spacings/ParagraphBelow", v))
        self.spnThemeTabWidth.valueChanged.connect(lambda v: self.setSetting("Spacings/TabWidth", v))
        
        # Update UI
        self.updateUIFromTheme()
        
        # Generate preview
        self._loadingTheme = False
        self.updatePreview()
        
    def setSetting(self, key, val):
        self._themeData[key] = val
        self.updatePreview()
        
    def updateUIFromTheme(self):
        self.txtThemeName.setText(self._themeData["Name"])
        
        # Window Background
        self.setButtonColor(self.btnThemWindowBackgroundColor, self._themeData["Background/Color"])
        i = self.cmbThemeBackgroundImage.findData(self._themeData["Background/ImageFile"], flags=Qt.MatchContains)
        if i != -1:
            self.cmbThemeBackgroundImage.setCurrentIndex(i)
        self.cmbThemBackgroundType.setCurrentIndex(self._themeData["Background/Type"])
        
        # Text background
        self.setButtonColor(self.btnThemeTextBackgroundColor, self._themeData["Foreground/Color"])
        self.spnThemeTextBackgroundOpacity.setValue(self._themeData["Foreground/Opacity"])
        self.spnThemeTextMargins.setValue(self._themeData["Foreground/Margin"])
        self.spnThemeTextPadding.setValue(self._themeData["Foreground/Padding"])
        self.cmbThemeTextPosition.setCurrentIndex(self._themeData["Foreground/Position"])
        self.spnThemeTextRadius.setValue(self._themeData["Foreground/Rounding"])
        self.spnThemeTextWidth.setValue(self._themeData["Foreground/Width"])
        
        # Text Options
        self.setButtonColor(self.btnThemeTextColor, self._themeData["Text/Color"])
        f = QFont()
        f.fromString(self._themeData["Text/Font"])
        self.cmbThemeFont.setCurrentFont(f)
        i = self.cmbThemeFontSize.findText(str(f.pointSize()))
        if i != -1:
            self.cmbThemeFontSize.setCurrentIndex(i)
        else:
            self.cmbThemeFontSize.addItem(str(f.pointSize()))
            self.cmbThemeFontSize.setCurrentIndex(self.cmbThemeFontSize.count()-1)
        self.setButtonColor(self.btnThemeMisspelledColor, self._themeData["Text/Misspelled"])
        
        # Paragraph Options
        self.chkThemeIndent.setCheckState(Qt.Checked if self._themeData["Spacings/IndendFirstLine"] else Qt.Unchecked)
        self.spnThemeLineSpacing.setEnabled(False)
        if self._themeData["Spacings/LineSpacing"] == 100:
            self.cmbThemeLineSpacing.setCurrentIndex(0)
        elif self._themeData["Spacings/LineSpacing"] == 150:
            self.cmbThemeLineSpacing.setCurrentIndex(1)
        elif self._themeData["Spacings/LineSpacing"] == 200:
            self.cmbThemeLineSpacing.setCurrentIndex(2)
        else:
            self.cmbThemeLineSpacing.setCurrentIndex(3)
            self.spnThemeLineSpacing.setEnabled(True)
            self.spnThemeLineSpacing.setValue(self._themeData["Spacings/LineSpacing"])
        self.spnThemeParaAbove.setValue(self._themeData["Spacings/ParagraphAbove"])
        self.spnThemeParaBelow.setValue(self._themeData["Spacings/ParagraphBelow"])
        self.spnThemeTabWidth.setValue(self._themeData["Spacings/TabWidth"])
        
    def populatesFontSize(self):
        self.cmbThemeFontSize.clear()
        s = list(range(6, 13)) + list(range(14,29, 2)) + [36, 48, 72]
        for i in s:
            self.cmbThemeFontSize.addItem(str(i))
        
    def updateThemeFont(self, v):
        f = self.cmbThemeFont.currentFont()
        s = self.cmbThemeFontSize.itemText(self.cmbThemeFontSize.currentIndex())
        if s:
            f.setPointSize(int(s))
            
        self._themeData["Text/Font"] = f.toString()
        self.updatePreview()
        
    def updateLineSpacing(self, i):
        if i == 0:
            self._themeData["Spacings/LineSpacing"] = 100
        elif i == 1:
            self._themeData["Spacings/LineSpacing"] = 150
        elif i == 2:
            self._themeData["Spacings/LineSpacing"] = 200
        elif i == 3:
            self._themeData["Spacings/LineSpacing"] = self.spnThemeLineSpacing.value()
        self.spnThemeLineSpacing.setEnabled(i == 3)
        self.updatePreview()
        
    def updateThemeBackground(self, i):
        img = self.cmbCorkImage.itemData(i)
        
        if img:
            self._themeData["Background/ImageFile"] = os.path.split(img)[1]
        else:
            self._themeData["Background/ImageFile"] = ""
        self.updatePreview()
        
    def getThemeColor(self, key):
        color = self._themeData[key]
        self.colorDialog = QColorDialog(QColor(color), self)
        color = self.colorDialog.getColor(QColor(color))
        if color.isValid():
            self._themeData[key] = color.name()
            self.updateUIFromTheme()
            self.updatePreview()
        
    def updatePreview(self):
        if self._loadingTheme:
            return
        
        currentScreen = qApp.desktop().screenNumber(self)
        screen = qApp.desktop().screenGeometry(currentScreen)
        
        px = createThemePreview(self._themeData, screen, self.lblPreview.size())
        self.lblPreview.setPixmap(px)
        
    def setButtonColor(self, btn, color):
        btn.setStyleSheet("background:{};".format(color))
        
    def saveTheme(self):
        settings = QSettings(self._editingTheme, QSettings.IniFormat)
        
        self._themeData["Name"] = self.txtThemeName.text()
        for key in self._themeData:
            settings.setValue(key, self._themeData[key])
            
        settings.sync()
        self.populatesThemesList()
        self.themeStack.setCurrentIndex(0)
        self._editingTheme = None
        
    def cancelEdit(self):
        self.themeStack.setCurrentIndex(0)
        self._editingTheme = None
    
    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        if self._editingTheme:
            self.updatePreview()