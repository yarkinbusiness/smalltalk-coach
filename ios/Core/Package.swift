// swift-tools-version:5.9
import Foundation
import PackageDescription

/// Plain-Foundation models and parsing logic shared by the SmallTalkCoach
/// app target. Deliberately has zero SwiftUI/UIKit/iOS-SDK-only
/// dependencies so it builds and tests with just the Swift toolchain
/// (Command Line Tools) — no Xcode / iOS SDK required. See
/// ios/SmallTalkCoach for the app target that consumes this package.
///
/// Test-target-only workaround: on a machine with only Command Line Tools
/// installed (no Xcode.app), `swift test` cannot find the `Testing`
/// module's framework unless its search path is passed explicitly — Xcode
/// normally supplies this automatically, but bare CLT does not. We detect
/// that one specific, known CLT location and add it only to CoreTests'
/// search paths (never to the `Core` library target that the app depends
/// on), so this has zero effect on the app target or on a future Xcode
/// build. If Xcode is later installed, this path simply won't exist and
/// the flags are skipped — Xcode will supply Testing.framework itself.
// Also disables the Testing<->Foundation cross-import overlay: this CLT
// install ships `_Testing_Foundation.framework` with no actual
// `.swiftmodule` inside it (an incomplete/broken artifact of this specific
// toolchain distribution), so any file that imports both `Testing` and
// `Foundation` fails to build unless overlay auto-loading is turned off.
// We don't rely on that overlay's Foundation-specific expectation
// diffing, so disabling it is harmless.
let commandLineToolsTestingFrameworksDir = "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"
let testTargetUnsafeFlags: [String] = FileManager.default.fileExists(atPath: commandLineToolsTestingFrameworksDir)
    ? ["-F", commandLineToolsTestingFrameworksDir, "-Xfrontend", "-disable-cross-import-overlays"]
    : []

let package = Package(
    name: "Core",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "Core", targets: ["Core"])
    ],
    targets: [
        .target(name: "Core"),
        .testTarget(
            name: "CoreTests",
            dependencies: ["Core"],
            swiftSettings: testTargetUnsafeFlags.isEmpty ? [] : [.unsafeFlags(testTargetUnsafeFlags)],
            linkerSettings: testTargetUnsafeFlags.isEmpty ? [] : [
                .unsafeFlags(testTargetUnsafeFlags + [
                    "-Xlinker", "-rpath", "-Xlinker", commandLineToolsTestingFrameworksDir
                ])
            ]
        )
    ]
)
