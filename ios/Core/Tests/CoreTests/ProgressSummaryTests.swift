import Testing
import Foundation
@testable import Core

struct ProgressSummaryTests {
    /// The normal shape returned by GET /users/{user_id}/progress/summary
    /// once a user has at least one real (non-parse_error) session --
    /// see backend's app/progress.py `build_progress_summary`.
    @Test func decodesWellFormedSummary() throws {
        let json = """
        {
            "session_count": 2,
            "current_focus_area": "reciprocity",
            "dimensions": {
                "warmth": [{"session_index": 0, "score": 4}, {"session_index": 1, "score": 5}],
                "curiosity": [{"session_index": 0, "score": 3}, {"session_index": 1, "score": 4}],
                "reciprocity": [{"session_index": 0, "score": 2}, {"session_index": 1, "score": 1}],
                "flow": [{"session_index": 0, "score": 4}, {"session_index": 1, "score": 4}]
            }
        }
        """.data(using: .utf8)!

        let summary = try JSONDecoder().decode(ProgressSummary.self, from: json)

        #expect(summary.sessionCount == 2)
        #expect(summary.currentFocusArea == "reciprocity")
        #expect(summary.dimensions["warmth"] == [
            ProgressDimensionPoint(sessionIndex: 0, score: 4),
            ProgressDimensionPoint(sessionIndex: 1, score: 5),
        ])
        #expect(summary.dimensions["reciprocity"]?.map(\.score) == [2, 1])
    }

    /// Brand-new-user / all-parse_error shape (see backend docstring): the
    /// route always returns 200 with this zero shape, never an error, so
    /// the client model must decode it cleanly too -- no optional
    /// `dimensions` dance, no crash on empty arrays.
    @Test func decodesEmptyHistoryShape() throws {
        let json = """
        {
            "session_count": 0,
            "current_focus_area": null,
            "dimensions": {
                "warmth": [],
                "curiosity": [],
                "reciprocity": [],
                "flow": []
            }
        }
        """.data(using: .utf8)!

        let summary = try JSONDecoder().decode(ProgressSummary.self, from: json)

        #expect(summary.sessionCount == 0)
        #expect(summary.currentFocusArea == nil)
        #expect(summary.dimensions["warmth"]?.isEmpty == true)
    }

    /// Documents the "gap" contract from the client's side: a dimension's
    /// array can have fewer points than session_count, and the present
    /// points' session_index values are what a chart must key off of --
    /// not raw array position -- so a gap in one dimension never shifts
    /// its remaining points relative to another dimension's line.
    @Test func perDimensionGapIsOmissionNotAPlaceholder() throws {
        let json = """
        {
            "session_count": 2,
            "current_focus_area": null,
            "dimensions": {
                "warmth": [{"session_index": 1, "score": 5}],
                "curiosity": [{"session_index": 0, "score": 3}, {"session_index": 1, "score": 5}],
                "reciprocity": [{"session_index": 0, "score": 3}, {"session_index": 1, "score": 5}],
                "flow": [{"session_index": 0, "score": 3}, {"session_index": 1, "score": 5}]
            }
        }
        """.data(using: .utf8)!

        let summary = try JSONDecoder().decode(ProgressSummary.self, from: json)

        #expect(summary.dimensions["warmth"]?.count == 1)
        #expect(summary.dimensions["warmth"]?.first?.sessionIndex == 1)
        #expect(summary.dimensions["curiosity"]?.count == 2)
    }

    /// A malformed `dimensions` value (a score that isn't an integer)
    /// should fail loudly, same strict-decoding philosophy as
    /// CoachReportTests.malformedScoresValueFailsToDecode.
    @Test func malformedScoreValueFailsToDecode() {
        let json = """
        {
            "session_count": 1,
            "current_focus_area": null,
            "dimensions": {
                "warmth": [{"session_index": 0, "score": "great job"}],
                "curiosity": [],
                "reciprocity": [],
                "flow": []
            }
        }
        """.data(using: .utf8)!

        #expect(throws: DecodingError.self) {
            try JSONDecoder().decode(ProgressSummary.self, from: json)
        }
    }
}
