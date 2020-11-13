if idaapi.IDA_SDK_VERSION <= 695:
    import idc
    import idaapi
    import binwalk
if idaapi.IDA_SDK_VERSION >= 700:
    import ida_idc
    import ida_idaapi
    import binwalk

    from idaapi import *
else:
    pass

# use 'try' here for compatibility with older API
# use Actions API for handlers
try:
    class OpHandler(idaapi.action_handler_t):
        def __init__(self):
            idaapi.action_handler_t.__init__(self)

        def activate(self, ctx):
            arg = None
            a = binwalk_t()
            a.opcode_scan(arg)
            return 1

        def update(self, ctx):
            return idaapi.AST_ENABLE_ALWAYS
except AttributeError:
    pass

# use 'try' here for compatibility with older API
# use Actions API for handlers
try:
    class SigHandler(idaapi.action_handler_t):
        def __init__(self):
            idaapi.action_handler_t.__init__(self)

        def activate(self, ctx):
            arg = None
            b = binwalk_t()
            b.signature_scan(arg)
            return 1

        def update(self, ctx):
            return idaapi.AST_ENABLE_ALWAYS
except AttributeError:
    pass

class binwalk_t(idaapi.plugin_t):
    flags = 0
    comment = "Scan the current IDB for file signatures"
    help = ""
    wanted_name = "Binwalk IDA Plugin"
    wanted_hotkey = ""

    def init(self):
        if idaapi.IDA_SDK_VERSION <= 695:
            self.menu_context_1 = idaapi.add_menu_item(
                "Search/", "binwalk opcodes", "", 0, self.opcode_scan, (None,))
            self.menu_context_2 = idaapi.add_menu_item(
                "Search/", "binwalk signatures", "", 0, self.signature_scan, (None,))

        if idaapi.IDA_SDK_VERSION >= 700:
            # populate action menus
            action_desc = idaapi.action_desc_t(
                'my:opaction',  # action name. This acts like an ID and must be unique
                'Binwalk opcodes',  # text for this action
                OpHandler(),  # the action handler
                '',  # optional shortcut key
                'Binwalk opcodes',  # optional action tooltip for menus/toolbar
                )

            # Register the action
            idaapi.register_action(action_desc)
            idaapi.attach_action_to_menu(
                'Search/',
                'my:opaction',
                idaapi.SETMENU_APP)

            # populate action menus
            action_desc = idaapi.action_desc_t(
                'my:sigaction',
                'Binwalk signatures',
                SigHandler(),
                '',
                'Binwalk signatures',
                )

            # Register the action
            idaapi.register_action(action_desc)
            idaapi.attach_action_to_menu(
                'Search/',
                'my:sigaction',
                idaapi.SETMENU_APP)

        else:
            pass

        return idaapi.PLUGIN_KEEP

    def term(self):
        if idaapi.IDA_SDK_VERSION <= 695:
            idaapi.del_menu_item(self.menu_context_1)
            idaapi.del_menu_item(self.menu_context_2)
        if idaapi.IDA_SDK_VERSION >= 700:
            idaapi.detach_action_from_menu(
                'Search/',
                'my:opaction')
            idaapi.detach_action_from_menu(
                'Search/',
                'my:sigaction')
        else:
            pass

        return None

    def run(self, arg):
        return None

    def signature_scan(self, arg):
        binwalk.scan(idc.GetIdbPath(), signature=True)

    def opcode_scan(self, arg):
        binwalk.scan(idc.GetIdbPath(), opcode=True)


def PLUGIN_ENTRY():
    return binwalk_t()
