""" Theme and styling configuration for the Todo application"""
import tkinter.font as tkfont

class Theme:
    
    
    class Color:
       
        BACKGROUND = "#fff8dc"
        TEXT = "#3b3b3b"
        ENTRY_BG = "#fdf6e3"
        BUTTON_BG = "#f5f5f5"
        BUTTON_HOVER = "#e0e0e0"
        PROGRESS_BAR_TROUGH = "#f0e9c7"
        BORDER = "#ddd"
        BORDER_FOCUS = "#aaa"
        FADED_TEXT = "#666"

    class Font:
     
        FAMILY = "Georgia"
        SIZE_NORMAL = 13
        SIZE_SMALL = 11

        @classmethod
        def get(cls, size: int = None, overstrike: bool = False) -> tkfont.Font:
            """設定されたdefault styleを取得 """
            if size is None:
                size = cls.SIZE_NORMAL
            return tkfont.Font(family=cls.FAMILY, size=size, overstrike=overstrike)

    class Layout:
        """Layoutとspacing設定 """
        PADDING_X = 10
        PADDING_Y = 5
        WIDGET_SPACING = 5
        BORDER_WIDTH = 6
