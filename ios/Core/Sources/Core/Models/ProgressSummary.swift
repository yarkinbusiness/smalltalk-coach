import Foundation

/// One point in a per-dimension score trend line -- see `ProgressSummary`.
///
/// `sessionIndex` is that session's zero-based position among the user's
/// chronological *valid* (non-parse_error) sessions -- NOT this point's
/// position within its own dimension's array. The backend (see backend's
/// app/progress.py `build_progress_summary`) omits a session_index from a
/// dimension's array entirely when that session didn't score that
/// dimension (a missing/garbage value coach.normalize_report dropped),
/// rather than sending a null/0 placeholder -- so one dimension's array
/// can be shorter than another's, and can name a different set of
/// session_indexes. Callers must plot/key off `sessionIndex`, never off
/// raw array position, so a gap in one dimension's data doesn't silently
/// shift or compress its remaining points relative to the other three.
public struct ProgressDimensionPoint: Codable, Hashable {
    public let sessionIndex: Int
    public let score: Int

    enum CodingKeys: String, CodingKey {
        case sessionIndex = "session_index"
        case score
    }

    public init(sessionIndex: Int, score: Int) {
        self.sessionIndex = sessionIndex
        self.score = score
    }
}

/// Body of GET /users/{user_id}/progress/summary (T11) -- see backend's
/// app/progress.py `build_progress_summary` for the full derivation
/// (chronological ordering, parse_error exclusion, and the per-dimension
/// "gap" representation documented on `ProgressDimensionPoint` above).
///
/// `dimensions` is decoded as a plain `[String: [ProgressDimensionPoint]]`
/// dictionary (keyed by dimension name -- "warmth", "curiosity",
/// "reciprocity", "flow") rather than four named properties, so a
/// dimension with zero scored sessions so far (an empty array server-side)
/// or, in principle, an unexpected/future dimension name is never a decode
/// failure -- mirroring the same "never invent a grade nobody produced,
/// never crash on a shape you don't recognize" philosophy as
/// coach.normalize_report on the backend. `session_count` and
/// `current_focus_area` both describe the same population of sessions the
/// `dimensions` series is computed over (see the backend docstring).
public struct ProgressSummary: Codable, Hashable {
    public let sessionCount: Int
    public let currentFocusArea: String?
    public let dimensions: [String: [ProgressDimensionPoint]]

    enum CodingKeys: String, CodingKey {
        case sessionCount = "session_count"
        case currentFocusArea = "current_focus_area"
        case dimensions
    }

    public init(sessionCount: Int, currentFocusArea: String?, dimensions: [String: [ProgressDimensionPoint]]) {
        self.sessionCount = sessionCount
        self.currentFocusArea = currentFocusArea
        self.dimensions = dimensions
    }
}
