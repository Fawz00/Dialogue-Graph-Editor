from PyQt6.QtGui import QColor

# ==========================================
# KONFIGURASI & STYLE (Mirip Unreal Engine)
# ==========================================

STYLES = {
    'grid_color': QColor(40, 40, 40),
    'bg_color': QColor(20, 20, 20),
    'node_header': QColor(40, 40, 40, 200),
    'node_body': QColor(15, 15, 15, 200),
    'node_shadow': QColor(255, 255, 255),
    'node_sel_border': QColor(255, 165, 0), # Orange selection
    'invalid_node_border': QColor(255, 0, 0), # Red border for invalid nodes
    'text_color': QColor(220, 220, 220),
    'socket_exec': QColor(255, 255, 255), # Putih untuk flow eksekusi
}

TYPE_COLORS = {
    "exec": QColor(255, 255, 255),    # Putih
    "String": QColor(255, 0, 212),    # Merah Muda/Magenta
    "Integer": QColor(43, 226, 172),      # Teal/Hijau Toska
    "Float": QColor(155, 255, 0),     # Hijau Neon
    "Boolean": QColor(172, 64, 0),       # Merah
    "Enum": QColor(0, 100, 255),      # Biru Tua
}