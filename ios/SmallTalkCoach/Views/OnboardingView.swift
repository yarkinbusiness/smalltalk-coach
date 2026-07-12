import Core
import SwiftUI

/// First-run, three-screen introduction shown exactly once per install
/// (gated by `OnboardingState.hasCompletedOnboarding` -- see `RootView`),
/// before the main `TabView` ever appears:
///
///   1. `WhatThisIsPage` -- what this app actually is, framed around the
///      four dimensions every session is graded on (see
///      backend/ARCHITECTURE.md's worker table and
///      `agents_setup.py`'s `COORDINATOR_SYSTEM` prompt).
///   2. `HowASessionWorksPage` -- how one session actually runs end to
///      end: live chat -> "End practice" -> coordinator + 4 graders ->
///      quote-backed report.
///   3. `StrugglePickPage` -- an optional "what do you struggle with
///      most?" pick, posted to `POST /users/{user_id}/onboarding`
///      (backend's `app/main.py` `onboard_user`) so it can seed the
///      user's very first coaching report if useful.
struct OnboardingView: View {
    /// Called exactly once, after `finish(struggle:)`'s network call
    /// resolves (success *or* failure) -- `RootView` uses this to flip
    /// `OnboardingState.hasCompletedOnboarding` to `true` and swap from
    /// this view to the main `TabView`.
    let onFinish: () -> Void

    @State private var page = 0
    @State private var isSubmitting = false

    private static let lastPage = 2

    var body: some View {
        VStack(spacing: 0) {
            TabView(selection: $page) {
                WhatThisIsPage()
                    .tag(0)
                HowASessionWorksPage()
                    .tag(1)
                StrugglePickPage(isSubmitting: isSubmitting, onPick: finish)
                    .tag(2)
            }
            .tabViewStyle(.page(indexDisplayMode: .always))
            .animation(.default, value: page)

            // The last page has its own two actions (a struggle pick, or
            // "Skip") that both finish onboarding directly -- there's
            // nothing for a generic "Next" button to do there.
            if page < Self.lastPage {
                Button("Next") {
                    withAnimation { page += 1 }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .padding()
            }
        }
    }

    /// `struggle` is `nil` for "Skip", or a stated `StrugglePick` --
    /// forwarded as-is to `APIClient.onboardUser`. Best-effort by design:
    /// a network failure here never blocks a first-time user from
    /// reaching the main app (the user's memory store also gets created
    /// lazily on their very first practice session regardless of whether
    /// this call ever succeeds -- see backend's `start_practice`); it just
    /// means this stated pick, if any, never got recorded.
    private func finish(struggle: StrugglePick?) {
        guard !isSubmitting else { return }
        isSubmitting = true
        Task {
            do {
                try await APIClient.shared.onboardUser(
                    userId: UserIdentity.current, struggle: struggle?.rawValue
                )
            } catch {
                // Intentionally swallowed -- see doc comment above.
            }
            isSubmitting = false
            onFinish()
        }
    }
}

/// The four struggle picks offered on `StrugglePickPage`. Raw values are
/// the exact wire strings backend's `memory.STRUGGLE_OPTIONS` keys on --
/// there is no shared source of truth between the two, so keep these in
/// sync by hand if either side's set of options ever changes.
enum StrugglePick: String, CaseIterable, Identifiable {
    case freezingOnOpeners = "freezing_on_openers"
    case onlyAskingQuestions = "only_asking_questions"
    case onlyTalkingAboutYourself = "only_talking_about_yourself"
    case awkwardExits = "awkward_exits"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .freezingOnOpeners: "Freezing on openers"
        case .onlyAskingQuestions: "Only asking questions"
        case .onlyTalkingAboutYourself: "Only talking about yourself"
        case .awkwardExits: "Awkward exits"
        }
    }

    /// Ties each pick back to the specific graded dimension it actually
    /// shows up in, so the picker reads as connected to the rest of the
    /// app's mechanics rather than a generic mood-check list.
    var subtitle: String {
        switch self {
        case .freezingOnOpeners:
            "Blanking on how to start -- shows up in your flow score."
        case .onlyAskingQuestions:
            "Interviewing instead of trading -- a curiosity-and-reciprocity thing."
        case .onlyTalkingAboutYourself:
            "Reciprocity tends to take the hit here."
        case .awkwardExits:
            "Hard to wrap it up cleanly -- also a flow thing."
        }
    }
}

// MARK: - Screen 1

private struct WhatThisIsPage: View {
    var body: some View {
        OnboardingPage(
            systemImage: "bubble.left.and.bubble.right.fill",
            title: "Practice small talk that actually transfers"
        ) {
            Text(
                "You'll talk to a realistic character in a live back-and-forth — a distracted "
                    + "coworker in an elevator, a regular between sets at the gym, a "
                    + "stranger seated next to you at a dinner party — and get graded on the "
                    + "four things that actually make small talk work:"
            )

            VStack(alignment: .leading, spacing: 12) {
                DimensionRow(
                    name: "Warmth",
                    detail: "How friendly and approachable you come across."
                )
                DimensionRow(
                    name: "Curiosity",
                    detail: "Whether you ask about them and build on their answers, instead of "
                        + "interrogating them."
                )
                DimensionRow(
                    name: "Reciprocity",
                    detail: "Whether you share enough of yourself to keep it balanced, not just "
                        + "extract answers."
                )
                DimensionRow(
                    name: "Flow",
                    detail: "How you open, transition between topics, and exit without it going "
                        + "awkward."
                )
            }
            .padding(.vertical, 4)

            Text(
                "Every scenario is graded on the same four dimensions, so you can see exactly "
                    + "which one is actually holding you back."
            )
        }
    }
}

private struct DimensionRow: View {
    let name: String
    let detail: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(name)
                .font(.subheadline.bold())
                .foregroundStyle(.primary)
            Text(detail)
                .font(.subheadline)
        }
    }
}

// MARK: - Screen 2

private struct HowASessionWorksPage: View {
    var body: some View {
        OnboardingPage(
            systemImage: "checkmark.message.fill",
            title: "Talk it out, then see the receipts"
        ) {
            Text(
                "Pick a scenario and start talking — it's a live chat with your practice "
                    + "partner in character, not a script or a quiz."
            )
            Text(
                "When you're done, tap **End practice**. A coordinator and four specialist "
                    + "graders read your actual turns and score each dimension."
            )
            Text(
                "Your report quotes your own words back to you — what worked, what to work "
                    + "on, and one small, concrete drill for next time. No vague feedback: "
                    + "every strength and focus area is backed by something you actually said."
            )
        }
    }
}

// MARK: - Screen 3

private struct StrugglePickPage: View {
    let isSubmitting: Bool
    let onPick: (StrugglePick?) -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Image(systemName: "target")
                    .font(.system(size: 40))
                    .foregroundStyle(Color.accentColor)
                    .frame(maxWidth: .infinity, alignment: .center)

                Text("One more thing before you start")
                    .font(.title2.bold())

                Text(
                    "If one of these already sounds like you, pick it — your first report can "
                        + "take it into account. Totally optional."
                )
                .font(.body)
                .foregroundStyle(.secondary)

                VStack(spacing: 10) {
                    ForEach(StrugglePick.allCases) { pick in
                        Button {
                            onPick(pick)
                        } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(pick.title)
                                    .font(.subheadline.bold())
                                    .foregroundStyle(.primary)
                                Text(pick.subtitle)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(12)
                            .background(
                                Color(.secondarySystemBackground),
                                in: RoundedRectangle(cornerRadius: 10)
                            )
                        }
                        .buttonStyle(.plain)
                        .disabled(isSubmitting)
                    }
                }

                Button("Skip") {
                    onPick(nil)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                .frame(maxWidth: .infinity)
                .disabled(isSubmitting)

                if isSubmitting {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                }
            }
            .padding()
            .padding(.bottom, 60)
        }
    }
}

// MARK: - Shared page chrome

/// Shared layout for the two read-only screens (`WhatThisIsPage`/
/// `HowASessionWorksPage`): a centered icon, a bold title, then whatever
/// body content the caller supplies -- kept generic over `Content` rather
/// than taking, say, `[String]` so each page can mix plain `Text` with a
/// structured block like `WhatThisIsPage`'s `DimensionRow` list.
private struct OnboardingPage<Content: View>: View {
    let systemImage: String
    let title: String
    let content: Content

    init(systemImage: String, title: String, @ViewBuilder content: () -> Content) {
        self.systemImage = systemImage
        self.title = title
        self.content = content()
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Image(systemName: systemImage)
                    .font(.system(size: 40))
                    .foregroundStyle(Color.accentColor)
                    .frame(maxWidth: .infinity, alignment: .center)

                Text(title)
                    .font(.title2.bold())

                VStack(alignment: .leading, spacing: 12) {
                    content
                }
                .font(.body)
                .foregroundStyle(.secondary)
            }
            .padding()
            .padding(.bottom, 60)
        }
    }
}
