[app]
title = 自动点击器
package.name = autoclient
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,ntplib,pyautogui
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.1
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.minapi = 21
android.api = 34
android.ndk = 27
android.enable_androidx = True
android.gradle = True
android.archs = arm64-v8a
android.log_handler = adb.log
android.add_build_dependencies = sdl2_ttf

[buildozer]
log_level = 1
