import idc
import idaapi
import binwalk

class binwalk_t(idaapi.plugin_t):
    flags = 0
    comment = "Scan the current IDB for file signatures"
    help = ""
    wanted_name = "Binwalk IDA Plugin"
    wanted_hotkey = ""

    def init(self):
        self.binwalk = binwalk.Modules(idc.GetIdbPath(), signature=True)
        self.menu_context = idaapi.add_menu_item("Search/", "binwalk scan", "Alt-9", 0, self.run, (None,))
        return idaapi.PLUGIN_KEEP

    def term(self):
        idaapi.del_menu_item(self.menu_context)
        return None

    def run(self, arg):
        self.binwalk.execute()

def PLUGIN_ENTRY():
    return binwalk_t()

