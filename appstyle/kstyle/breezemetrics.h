/*
 * SPDX-FileCopyrightText: 2014 Hugo Pereira Da Costa <hugo.pereira@free.fr>
 * SPDX-FileCopyrightText: 2020 Noah Davis <noahadvs@gmail.com>
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#pragma once

#include <QtGlobal>

namespace Breeze
{
//* standard pen widths
struct PenWidth {
    /* Using 1 instead of slightly more than 1 causes symbols drawn with
     * pen strokes to look skewed. The exact amount added does not matter
     * as long as it isn't too visible. Even with QPen::setCosmetic(true),
     * 1px pen widths still look slightly worse.
     */
    // The standard pen stroke width for symbols.
    static constexpr qreal Symbol = 1.001;

    // The standard pen stroke width for frames.
    static constexpr qreal Frame = 1.001;

    // The standard pen stroke width for shadows.
    static constexpr qreal Shadow = 1.001;

    // A value for pen width arguments to make it clear that there is no pen stroke
    static constexpr int NoPen = 0;
};

//* macOS 27 tokens
struct Tokens {
    // "Scrollbar": overlay pill, no arrows.
    // Horizontal 29x6 rx3, vertical 6x29 rx3, white at 55% (dark). Light mode draws the pill in the text colour at the same alpha.
    // Hover: macOS widens the thumb and fades a track in behind it while the pointer is over the bar. 6 -> 10px here.
    struct ScrollBar {
        static constexpr int Thickness = 6;     // pill thickness, rx = 3 (fully round)
        static constexpr int MinLength = 29;    // pill length
        static constexpr qreal Alpha = 0.55;    // fill alpha
        static constexpr int HoverThickness = 10; // pill thickness while the pointer is over the bar (animated 6 -> 10)
        static constexpr int TrackAlphaDark = 38;   // hover track, dark: rgba(201,201,201,38)
        static constexpr int TrackAlphaLight = 191; // hover track, light: rgba(250,250,250,191)
        static constexpr int TrackEdgeAlpha = 20;   // 1px line on the content side of the track (black light / white dark)
    };
    // "Menu". Corner radius deliberately NOT taken from macOS (19): Halcyon keeps Surface_Radius.
    struct Menu {
        static constexpr int ShadowOffsetY = 8;     // dy
        static constexpr int ShadowBlurSigma = 24;  // stdDeviation
        static constexpr qreal ShadowOpacity = 0.25; // black
        static constexpr qreal RimWidth = 0.5;      // outer ring, dilate 0.5 (the +-1.25 side shadows end up inside it)
        static constexpr int RimRgb = 0xDB;         // #DBDBDB
    };
    // "Alerts". Radius deliberately NOT taken from macOS (34): Halcyon keeps its own.
    // Inner band + hairline: Helper::renderAlertBand (QMessageBox) and tools/gen_alert.py (Plasma dialog background).
    struct Alert {
        // Baked into the SVGs by tools/gen_alert.py (not read by C++):
        //   fill: white 70% (alpha 179, lighten) + #BFBFBF 10% (alpha 26, darken)
        //   side shadows: 1.25px #DBDBDB, left and right
        //   drop shadow: black 25% (alpha 64), offset Y 18, blur sigma 24
        static constexpr int HairlineRgb = 0xDB;       // #DBDBDB, 0.5px ring (plus-darker)
        static constexpr int InnerBandRgb = 0x28;      // #282828 plus-lighter, offset +-40, blur 5 (top and bottom light band)
        static constexpr int InnerBandBlurSigma = 5;
    };
};

//* metrics
struct Metrics {
    // general
    static constexpr int ArrowSize = 10;
    static constexpr int SmallArrowSize = 5;

    // frames
    static constexpr int Frame_FrameWidth = 2;
    // Geometry only (tab overlaps, header separators, view column clamps). Drawn corners use Control_Radius / Surface_Radius.
    static constexpr int Frame_FrameRadius = 5;

    // Design tokens
    // The radii are defined in tools/radii.py, and `python3 tools/radii.py --check` fails if these constants drift from it.
    // Control tier: buttons, fields, tabs and small pieces inside a surface. Plasma tooltips and dock labels use it too.
    static constexpr int Control_Radius = 6;
    // Surface tier: menus, alerts and popups. Same arc as the window decoration, the Plasma dialogs and the dock.
    static constexpr int Surface_Radius = 10;
    // The small control height (36px). Change this one number for 40px.
    static constexpr int Control_Height = 36;
    // Horizontal padding inside a push button (the vertical one is Button_MarginWidth)
    static constexpr int Button_PaddingX = 12;

    // icons: the style used to ask for 16px everywhere, which read as small next to 13px text
    static constexpr int Icon_Small = 20;   // buttons, menus, lists, tabs, headers
    static constexpr int Icon_ToolBar = 24; // toolbar buttons (24 + 2*8 = a 40px icon button)

    // layout
    static constexpr int Layout_TopLevelMarginWidth = 16; // was 10: gutter is 16
    static constexpr int Layout_ChildMarginWidth = 8; // was 6
    static constexpr int Layout_DefaultSpacing = 8; // was 6: gap-2

    // line editors
    static constexpr int LineEdit_FrameWidth = 6; // Breeze value: search and text fields keep stock Breeze height

    // menu items
    static constexpr int Menu_FrameWidth = 0;
    static constexpr int MenuItem_MarginWidth = 5; // SVG: text and separators sit 11px from the panel edge (6 padding + 5)
    static constexpr int MenuItem_HighlightGap = 6; // was 4: menu panel padding is 6
    static constexpr int MenuItem_ExtraLeftMargin = 0;
    static constexpr int MenuItem_MarginHeight = 2; // SVG / screenshot: 24px rows (20px icon + 2*2)
    static constexpr int MenuItem_ItemSpacing = 10; // was 2: icon-to-label gap
    static constexpr int MenuItem_AcceleratorSpace = 16;
    static constexpr int MenuItem_TextLeftMargin = 0;

    // combobox
    static constexpr int ComboBox_FrameWidth = 6; // Breeze value, matches the line edit
    static constexpr int ComboBox_ItemMarginWidth = 4; // was 3

    // spinbox
    static constexpr int SpinBox_FrameWidth = LineEdit_FrameWidth;
    static constexpr int SpinBox_ArrowButtonWidth = 20;

    // groupbox title margin
    static constexpr int GroupBox_TitleMarginWidth = 8; // was 4

    // buttons
    static constexpr int Button_MinWidth = 80;
    static constexpr int Button_MarginWidth = 6;
    static constexpr int Button_ItemSpacing = 8; // was 4: the icon was touching the label

    // tool buttons
    static constexpr int ToolButton_MarginWidth = 8; // was 6: 24px icon + 2*8 = a 40px icon button
    static constexpr int ToolButton_ItemSpacing = 6; // was 4
    static constexpr int ToolButton_InlineIndicatorWidth = 12;

    // menu button indicator
    static constexpr int MenuButton_IndicatorWidth = 20;

    // checkboxes and radio buttons
    static constexpr int CheckBox_Size = 20; // 2px focus margin each side, so the drawn box is 16px like macOS
    static constexpr int CheckBox_FocusMarginWidth = 2;
    static constexpr int CheckBox_ItemSpacing = 8; // was 4
    static constexpr int CheckBox_Radius = 4; // 4px on a 16px box, like macOS

    // menubar items
    static constexpr int MenuBarItem_MarginWidth = 12; // was 10
    static constexpr int MenuBarItem_MarginHeight = 8; // was 6

    // scrollbars
    static constexpr int ScrollBar_Extend = 14; // room for the 10px hover pill + 2px either side (6px resting pill sits centred; was 21)
    static constexpr int ScrollBar_SliderWidth = Tokens::ScrollBar::Thickness;
    static constexpr int ScrollBar_MinSliderHeight = Tokens::ScrollBar::MinLength;
    static constexpr int ScrollBar_NoButtonHeight = 0;
    static constexpr int ScrollBar_SingleButtonHeight = ScrollBar_Extend;
    static constexpr int ScrollBar_DoubleButtonHeight = 2 * ScrollBar_Extend;

    // toolbars
    static constexpr int ToolBar_FrameWidth = 0;
    static constexpr int ToolBar_HandleExtent = 10;
    static constexpr int ToolBar_HandleWidth = 6;
    static constexpr int ToolBar_SeparatorWidth = 8;
    static constexpr int ToolBar_ItemMargin = 6;
    static constexpr int ToolBar_ItemSpacing = 4; // was 0: toolbar buttons no longer touch

    // progressbars
    static constexpr int ProgressBar_BusyIndicatorSize = 14;
    static constexpr int ProgressBar_Thickness = 6;
    static constexpr int ProgressBar_ItemSpacing = 8; // was 4

    // mdi title bar
    static constexpr int TitleBar_MarginWidth = 4;

    // sliders
    static constexpr int Slider_TickMarginWidth = 4;
    static constexpr int Slider_GrooveThickness = 4; // thin groove, as on macOS (was 6)
    static constexpr int Slider_ControlThickness = 20; // knob length along the track
    static constexpr int Slider_KnobThickness = 16;    // knob size across the track (pill 20x16)
    static constexpr int Slider_ShadowMargin = 4;      // room above/below the knob so its drop shadow is not clipped
    static constexpr int Dial_KnobSize = 24;           // dial knob (24px circle with 2x6 notch)

    // tabbar
    static constexpr int TabBar_TabMarginHeight = 8; // was 4
    static constexpr int TabBar_TabMarginWidth = 14; // was 8
    static constexpr int TabBar_TabMinWidth = 80;
    static constexpr int TabBar_TabMinHeight = 36; // was 30
    static constexpr int TabBar_StaticTabMinHeight = 38; // was 34
    static constexpr int TabBar_TabItemSpacing = 8;
    static constexpr int TabBar_TabOverlap = 1;
    static constexpr int TabBar_BaseOverlap = 2;
    static constexpr int TabBar_ActiveEffectSize = 3;
    // drawn corner radius of a tab (control tier, see tools/radii.py)
    static constexpr int TabBar_TabRadius = 6;

    // tab widget
    static constexpr int TabWidget_MarginWidth = 3;

    // toolbox
    static constexpr int ToolBox_TabMinWidth = 80;
    static constexpr int ToolBox_TabItemSpacing = 8; // was 4
    static constexpr int ToolBox_TabMarginWidth = 12; // was 8

    // tooltips
    static constexpr int ToolTip_FrameWidth = 8; // was 3: tooltip padding

    // list headers
    static constexpr int Header_MarginWidth = 8; // was 6
    static constexpr int Header_ItemSpacing = 8; // was 4
    static constexpr int Header_ArrowSize = ArrowSize;

    // tree view
    static constexpr int ItemView_ArrowSize = ArrowSize;
    static constexpr int ItemView_ItemMarginLeft = 4; // was 2
    static constexpr int ItemView_ItemMarginRight = 4; // was 2
    // Normal margin height is 2 to have rows spaced 4
    // First and last items will have a bigger top/bottom margin for consistent borders with the outside frame
    static constexpr int ItemView_FirstItemTopMarginHeight = 4; // was 2
    static constexpr int ItemView_ItemMarginTop = 2; // was 1: rows sit 4px apart
    static constexpr int ItemView_ItemMarginBottom = 2; // was 1
    static constexpr int ItemView_ItemPaddingWidth = 8; // was 2: room for the 14px row corners
    static constexpr int ItemView_ItemPaddingHeight = 6; // was 2

    // splitter
    static constexpr int Splitter_SplitterWidth = 1;

    // shadow dimensions
    static constexpr int Shadow_Overlap = 2;

    // Value used to blend background and foreground,
    // used for hover effects and similar.
    static constexpr qreal Blend_Value = 0.3;

    static constexpr qreal Focus_LightenColorValue = 110;
};
}
