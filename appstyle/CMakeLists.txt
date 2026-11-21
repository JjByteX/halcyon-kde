cmake_minimum_required(VERSION 3.16)
project(halcyonglass)
set(PROJECT_VERSION "0.1.0")

# Same requirements as the Breeze v6.8.3 this is forked from.
set(KF6_MIN_VERSION "6.30.0")
set(KDE_COMPILERSETTINGS_LEVEL "5.82")
set(QT_MIN_VERSION "6.11.0")

find_package(ECM ${KF6_MIN_VERSION} REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH})

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FeatureSummary)
set(QT_MAJOR_VERSION 6)
include(KDEInstallDirs6)
include(KDECMakeSettings)
include(ECMQtDeclareLoggingCategory)

find_package(Qt6 ${QT_MIN_VERSION} REQUIRED CONFIG COMPONENTS Widgets Core)
find_package(Qt6 ${QT_MIN_VERSION} CONFIG OPTIONAL_COMPONENTS DBus Quick)
set(HAVE_QTDBUS ${Qt6DBus_FOUND})
set(BREEZE_HAVE_QTQUICK ${Qt6Quick_FOUND})

find_package(KF6 ${KF6_MIN_VERSION} REQUIRED COMPONENTS
    CoreAddons ColorScheme Config GuiAddons IconThemes WindowSystem)
find_package(KF6FrameworkIntegration ${KF6_MIN_VERSION} CONFIG)
set(BREEZE_HAVE_KSTYLE ${KF6FrameworkIntegration_FOUND})

add_subdirectory(kstyle kstyle6)
add_subdirectory(libbreezecommon libbreezecommon6)

feature_summary(WHAT ALL FATAL_ON_MISSING_REQUIRED_PACKAGES)
