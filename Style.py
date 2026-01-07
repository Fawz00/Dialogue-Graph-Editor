from PyQt6.QtGui import QColor

from Core.Enums.DataType import DataType

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

    # Common UI colors
    'primary_text': QColor(230, 230, 230),
    'secondary_text': QColor(150, 150, 150),
    'error': QColor(255, 100, 100),
    'warning': QColor(255, 200, 100),
    'success': QColor(100, 255, 100),
}

DATA_TYPE_COLORS = {
    DataType.STRING: QColor(255, 0, 212),    # Merah Muda/Magenta
    DataType.INT: QColor(43, 226, 172),      # Teal/Hijau Toska
    DataType.FLOAT: QColor(155, 255, 0),     # Hijau Neon
    DataType.BOOL: QColor(172, 64, 0),       # Merah
    DataType.ENUM: QColor(0, 100, 255),      # Biru Tua
    DataType.ARRAY: QColor(255, 165, 0),      # Oranye
    DataType.STRUCT: QColor(200, 0, 255),    # Ungu
}

LOG_LEVEL_COLORS = {
    'info': QColor(200, 200, 200),      # Abu-abu
    'warning': QColor(255, 200, 100),   # Kuning
    'error': QColor(255, 100, 100),     # Merah
}