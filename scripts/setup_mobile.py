"""Generate Flutter's native wrappers while preserving the supplied application."""
import pathlib,subprocess,re,shutil
root=pathlib.Path(__file__).resolve().parents[1]/'mobile'
if not shutil.which('flutter'):raise SystemExit('Install Flutter stable and put flutter on PATH first: https://docs.flutter.dev/get-started/install')
keep={p:p.read_bytes() for p in [root/'pubspec.yaml',*root.glob('lib/*.dart')]}
try:subprocess.run(['flutter','create','--project-name','scamshield','--platforms','android,ios','.'],cwd=root,check=True)
finally:
    for p,data in keep.items():p.write_bytes(data)
# Remove generated counter-demo tests, which describe a different application.
test=root/'test/widget_test.dart'
if test.exists():test.unlink()
for p in (root/'android/app').glob('build.gradle*'):
    s=p.read_text();s=s.replace('minSdk = flutter.minSdkVersion','minSdk = 23').replace('minSdkVersion flutter.minSdkVersion','minSdkVersion 23')
    p.write_text(s)
manifest=root/'android/app/src/main/AndroidManifest.xml'
s=manifest.read_text()
if 'android.permission.INTERNET' not in s:s=s.replace('<application','<uses-permission android:name="android.permission.INTERNET"/>\n    <application',1)
manifest.write_text(s)
# Development-only cleartext access for the Android emulator. Release stays HTTPS-only.
debug=root/'android/app/src/debug/AndroidManifest.xml';debug.parent.mkdir(parents=True,exist_ok=True)
debug.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-permission android:name="android.permission.INTERNET"/><application android:usesCleartextTraffic="true"/></manifest>')
plist=root/'ios/Runner/Info.plist'
s=plist.read_text().replace('</dict>','<key>NSPhotoLibraryUsageDescription</key><string>Select a screenshot to recognise text on your device.</string>\n</dict>',1)
plist.write_text(s)
project=root/'ios/Runner.xcodeproj/project.pbxproj'
s=project.read_text();s=re.sub(r'IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+;', 'IPHONEOS_DEPLOYMENT_TARGET = 15.5;',s);project.write_text(s)
pod=root/'ios/Podfile'
if pod.exists():
    s=pod.read_text();s=re.sub(r"#?\s*platform :ios, '[^']+'","platform :ios, '15.5'",s)
    if "platform :ios" not in s:s="platform :ios, '15.5'\n"+s
    pod.write_text(s)
subprocess.run(['flutter','pub','get'],cwd=root,check=True)
print('Native wrappers ready. Run flutter analyze, then flutter run with API_BASE_URL. See README.md for platform notes.')
