################# includes #################
include_directories(
  animations
)

include_directories(${CMAKE_SOURCE_DIR}/libbreezecommon)
include_directories(${CMAKE_BINARY_DIR}/libbreezecommon)

################# configuration #################
configure_file(config-breeze.h.cmake ${CMAKE_CURRENT_BINARY_DIR}/config-breeze.h )

########### next target ###############
set(halcyonglass_PART_SRCS
    animations/breezeanimation.cpp
    animations/breezeanimations.cpp
    animations/breezeanimationdata.cpp
    animations/breezebaseengine.cpp
    animations/breezebusyindicatordata.cpp
    animations/breezebusyindicatorengine.cpp
    animations/breezedialdata.cpp
    animations/breezedialengine.cpp
    animations/breezeenabledata.cpp
    animations/breezegenericdata.cpp
    animations/breezeheaderviewdata.cpp
    animations/breezeheaderviewengine.cpp
    animations/breezescrollbardata.cpp
    animations/breezescrollbarengine.cpp
    animations/breezespinboxengine.cpp
    animations/breezespinboxdata.cpp
    animations/breezestackedwidgetdata.cpp
    animations/breezestackedwidgetengine.cpp
    animations/breezetabbarengine.cpp
    animations/breezetabbardata.cpp
    animations/breezetoolboxengine.cpp
    animations/breezetransitiondata.cpp
    animations/breezetransitionwidget.cpp
    animations/breezewidgetstateengine.cpp
    animations/breezewidgetstatedata.cpp
    breezeaddeventfilter.h
    breezeblurhelper.cpp
    breezeframeshadow.cpp
    breezehelper.cpp
    breezemdiwindowshadow.cpp
    breezemnemonics.cpp
    breezepropertynames.cpp
    breezeshadowhelper.cpp
    breezesplitterproxy.cpp
    breezestyle.cpp
    breezestyleplugin.cpp
    breezetileset.cpp
    breezewindowmanager.cpp
    breezetoolsareamanager.cpp
)

kconfig_add_kcfg_files(halcyonglass_PART_SRCS breezestyleconfigdata.kcfgc)


add_library(halcyonglass${QT_MAJOR_VERSION} MODULE ${halcyonglass_PART_SRCS})

ecm_qt_declare_logging_category(halcyonglass${QT_MAJOR_VERSION}
    HEADER
        breeze_logging.h
    IDENTIFIER
        BREEZE
    CATEGORY_NAME
        halcyonglass${QT_MAJOR_VERSION}
    DEFAULT_SEVERITY
        Warning
)

target_link_libraries(halcyonglass${QT_MAJOR_VERSION}
    Qt${QT_MAJOR_VERSION}::Core
    Qt${QT_MAJOR_VERSION}::Gui
    Qt${QT_MAJOR_VERSION}::Widgets
)

if(HAVE_QTDBUS)
    target_link_libraries(halcyonglass${QT_MAJOR_VERSION}
        Qt${QT_MAJOR_VERSION}::DBus
    )
endif()

if( BREEZE_HAVE_QTQUICK )
    target_link_libraries(halcyonglass${QT_MAJOR_VERSION} 
        Qt${QT_MAJOR_VERSION}::Quick
        KF${QT_MAJOR_VERSION}::CoreAddons
    )
endif()

target_link_libraries(halcyonglass${QT_MAJOR_VERSION}
    KF${QT_MAJOR_VERSION}::CoreAddons
    KF${QT_MAJOR_VERSION}::ConfigCore
    KF${QT_MAJOR_VERSION}::ConfigGui
    KF${QT_MAJOR_VERSION}::GuiAddons
    KF${QT_MAJOR_VERSION}::IconThemes
    KF${QT_MAJOR_VERSION}::WindowSystem
)

target_link_libraries(halcyonglass${QT_MAJOR_VERSION} KF6::ColorScheme)

target_link_libraries(halcyonglass${QT_MAJOR_VERSION} breezecommon${QT_MAJOR_VERSION})

if(KF${QT_MAJOR_VERSION}FrameworkIntegration_FOUND)
    target_link_libraries(halcyonglass${QT_MAJOR_VERSION}  KF${QT_MAJOR_VERSION}::Style)
endif()


########### install files ###############
install(TARGETS halcyonglass${QT_MAJOR_VERSION}  DESTINATION ${KDE_INSTALL_QTPLUGINDIR}/styles/)
install(FILES halcyonglass.themerc  DESTINATION  ${KDE_INSTALL_DATADIR}/kstyle/themes)

########### subdirectories ###############


