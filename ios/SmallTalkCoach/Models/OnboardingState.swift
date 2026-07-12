import Foundation

/// Whether this device has already been through the first-run onboarding
/// flow (see OnboardingView) -- the same per-device, no-login UserDefaults
/// pattern as `UserIdentity.current` above (this app has no accounts, so
/// "this device/install" is the only identity that exists).
///
/// `false` (the default `UserDefaults.bool(forKey:)` value for a key that's
/// never been set) until `OnboardingView`'s flow actually *finishes* --
/// either a stated struggle pick or a tap on "Skip" on its third screen --
/// not the moment onboarding merely starts. That means force-quitting the
/// app mid-onboarding shows it again on next launch (nothing was ever
/// completed) rather than silently skipping it, while a normal completed
/// run shows it exactly once for the lifetime of the install.
enum OnboardingState {
    private static let key = "smalltalk_coach_has_onboarded"

    static var hasCompletedOnboarding: Bool {
        get { UserDefaults.standard.bool(forKey: key) }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }
}
