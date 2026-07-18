# SmallTalkCoach iOS app

Generate the Xcode project from the repository root:

```sh
xcodegen generate --spec ios/project.yml
```

Build for an iOS Simulator:

```sh
xcodebuild build -project ios/SmallTalkCoach.xcodeproj -scheme SmallTalkCoach -destination 'generic/platform=iOS Simulator' -derivedDataPath "$TMPDIR/stc-derived" CODE_SIGNING_ALLOWED=NO
```

Run unit tests on the configured simulator:

```sh
xcodebuild test -project ios/SmallTalkCoach.xcodeproj -scheme SmallTalkCoach -destination 'platform=iOS Simulator,name=iPhone 16,OS=18.2' -derivedDataPath "$TMPDIR/stc-derived" CODE_SIGNING_ALLOWED=NO
```

The app uses `http://127.0.0.1:8000` by default. Set the `smalltalkCoach.apiBaseURL` UserDefaults key to override the backend base URL during development.
