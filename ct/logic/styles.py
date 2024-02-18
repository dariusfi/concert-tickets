from reportlab.lib.styles import _baseFontNameB, getSampleStyleSheet

# Styles for Reportlab
sample_styles = getSampleStyleSheet()

STYLE_SMALL = sample_styles["Normal"].clone("style_small")

STYLE_SMALL_CENTERED = sample_styles["Normal"].clone("style_small__centered")
STYLE_SMALL_CENTERED.alignment = 1

STYLE_NORMAL = sample_styles["Normal"].clone("style_normal")
STYLE_NORMAL.fontSize = 12
STYLE_NORMAL.leading = 14

STYLE_NORMAL_BOLD = sample_styles["Normal"].clone("style_normal_bold")
STYLE_NORMAL_BOLD.fontSize = 12
STYLE_NORMAL_BOLD.fontName = _baseFontNameB
STYLE_NORMAL_BOLD.leading = 14

STYLE_HEADING = sample_styles["Heading1"].clone("style_heading")
STYLE_HEADING.spaceAfter = 16

STYLE_IMPORTANT = sample_styles["Normal"].clone("style_important")
STYLE_IMPORTANT.fontSize = 14
STYLE_IMPORTANT.fontName = _baseFontNameB
STYLE_IMPORTANT.spaceAfter = 5
