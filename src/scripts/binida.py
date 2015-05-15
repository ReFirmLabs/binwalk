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
        self.menu_context_1 = idaapi.add_menu_item("Search/", "binwalk opcodes", "", 0, self.opcode_scan, (None,))
        self.menu_context_2 = idaapi.add_menu_item("Search/", "binwalk signatures", "", 0, self.signature_scan, (None,))
        return idaapi.PLUGIN_KEEP

    def term(self):
        idaapi.del_menu_item(self.menu_context_1)
        idaapi.del_menu_item(self.menu_context_2)
        return None

    def run(self, arg):
        return None

    def signature_scan(self, arg):
        binwalk.scan(idc.GetIdbPath(), signature=True)

    def opcode_scan(self, arg):
        binwalk.scan(idc.GetIdbPath(), opcode=True)

def PLUGIN_ENTRY():
    return binwalk_t()

