import SwiftUI

enum MotionPolicy {
    static func animation(_ base: Animation, reduceMotion: Bool) -> Animation? {
        reduceMotion ? nil : base
    }
}

private struct MotionAwareAnimation<Value: Equatable>: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let animation: Animation
    let value: Value

    func body(content: Content) -> some View {
        content.animation(MotionPolicy.animation(animation, reduceMotion: reduceMotion), value: value)
    }
}

extension View {
    func motionAwareAnimation<Value: Equatable>(_ animation: Animation, value: Value) -> some View {
        modifier(MotionAwareAnimation(animation: animation, value: value))
    }
}

#Preview("Motion policy — Animated") {
    MotionPolicyPreview(reduceMotion: false)
}

#Preview("Motion policy — Reduce Motion") {
    MotionPolicyPreview(reduceMotion: true)
}

private struct MotionPolicyPreview: View {
    let reduceMotion: Bool
    @State private var isMoved = false

    var body: some View {
        VStack(spacing: 24) {
            circle

            Button("Move circle") {
                isMoved.toggle()
            }
        }
        .padding()
    }

    @ViewBuilder
    private var circle: some View {
        if reduceMotion {
            Circle()
                .fill(.indigo)
                .frame(width: 56, height: 56)
                .offset(x: isMoved ? 72 : -72)
                .animation(
                    MotionPolicy.animation(.easeInOut(duration: 0.3), reduceMotion: true),
                    value: isMoved
                )
        } else {
            Circle()
                .fill(.indigo)
                .frame(width: 56, height: 56)
                .offset(x: isMoved ? 72 : -72)
                .motionAwareAnimation(.easeInOut(duration: 0.3), value: isMoved)
        }
    }
}
