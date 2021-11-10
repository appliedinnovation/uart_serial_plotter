def menubar_init(self):
    self.menus = {}
    self.menubar = self.menuBar()


def menubar_add_menu(self, menu_name):
    """
    :param in string menu_name: name of the menu, shortcut (denoted by &) optional (note that the & will be stripped)
    """
    dict_name = menu_name.strip("&")
    if dict_name not in self.menus:
        self.menus[dict_name] = self.menubar.addMenu(menu_name)


def menubar_get_menu(self, menu_name):
    """
    :param in string menu_name: name of the menu, shortcut (denoted by &) optional (note that the & will be stripped)
    """
    dict_name = menu_name.strip("&")
    return self.menus[dict_name]


def menu_add_action(self, menu_name, menu_action):
    """
    :param in string menu_name: name used to create the menu from :func:`Editor.menubar_add_menu`.
    :param in Action menu_action: :class:`action.Action` object to bind to the menu.
    """
    dict_name = menu_name.strip("&")
    if dict_name in self.menus:
        self.menus[dict_name].addAction(menu_action)
