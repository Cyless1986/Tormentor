$ErrorActionPreference = 'Stop'
$androidProject = $PSScriptRoot
$env:JAVA_HOME = (Get-ChildItem "$androidProject/tools/java" -Directory | Select-Object -First 1).FullName
$env:GRADLE_USER_HOME = "$androidProject/tools/gradle-home"
$originalAndroidHome = Join-Path $env:USERPROFILE '.android'
$env:ANDROID_USER_HOME = if (Test-Path (Join-Path $originalAndroidHome 'debug.keystore')) { $originalAndroidHome } else { "$androidProject/tools/android-home" }
New-Item -ItemType Directory -Force $env:ANDROID_USER_HOME | Out-Null
& "$androidProject/tools/gradle/gradle-8.9/bin/gradle.bat" -p $androidProject --no-daemon assembleDebug testDebugUnitTest lintDebug
if ($LASTEXITCODE -ne 0) { throw 'Android-Build fehlgeschlagen.' }
Copy-Item "$androidProject/app/build/outputs/apk/debug/app-debug.apk" "$androidProject/Tormentor-Android.apk" -Force
Write-Output "APK: $androidProject/Tormentor-Android.apk"
