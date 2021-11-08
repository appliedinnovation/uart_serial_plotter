from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction


class Action(QAction):
    """
    Wrapper class for Qt's QAction so that other library code doesn't have to
    import pyQt.  (Unnecessary?)
    """

    def __init__(self, icon_file, text, parent):
        super(Action, self).__init__(QtGui.QIcon(icon_file), text, parent)


def action_init(self):
    self.actions = {}


def action_create(self, action_name, icon, title, actionFunc, tooltip, shortcut):
    """
    :param in string action_name: unique name used as a key to store the action
    :param in string icon: filename for the action's icon
    :param in string title: full title of the action for display (menu, toolbar, context menu, etc.)
    :param in actionFunc: callback function for the action
    :param in string shortcut: Qt formatted shortcut for the action, e.g. 'Ctrl+O'.
    """
    self.actions[action_name] = Action(icon, title, self)
    if tooltip:
        self.actions[action_name].setStatusTip(tooltip)
    if shortcut:
        self.actions[action_name].setShortcut(shortcut)
    self.actions[action_name].triggered.connect(actionFunc)
