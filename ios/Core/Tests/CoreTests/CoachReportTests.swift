import Testing
import Foundation
@testable import Core

struct CoachReportTests {
    /// The normal shape returned by `POST /practice/sessions/{id}/end` when
    /// the coach model's output parsed cleanly.
    @Test func decodesWellFormedReport() throws {
        let json = """
        {
            "scores": {"warmth": 4, "curiosity": 3},
            "strengths": ["Asked a good follow-up question"],
            "focus_areas": ["Try pausing before responding"],
            "drill_suggestion": "Practice one open-ended question per reply",
            "raw": null,
            "parse_error": null
        }
        """.data(using: .utf8)!

        let report = try JSONDecoder().decode(CoachReport.self, from: json)

        #expect(report.scores == ["warmth": 4, "curiosity": 3])
        #expect(report.strengths == ["Asked a good follow-up question"])
        #expect(report.focusAreas == ["Try pausing before responding"])
        #expect(report.drillSuggestion == "Practice one open-ended question per reply")
        #expect(report.rawText == nil)
        #expect(report.parseError == nil)
    }

    /// `parse_error` shape: the backend falls back to this when the coach
    /// model's reply couldn't be parsed as structured JSON — scores /
    /// strengths / focus_areas / drill_suggestion are still required keys
    /// by CoachReport's Decodable synthesis (no defaults), so the backend
    /// must send empty collections/string alongside `raw` + `parse_error`.
    /// This test documents that contract from the client's side.
    @Test func decodesParseErrorFallbackShape() throws {
        let json = """
        {
            "scores": {},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": "the model's raw, non-JSON reply text",
            "parse_error": true
        }
        """.data(using: .utf8)!

        let report = try JSONDecoder().decode(CoachReport.self, from: json)

        #expect(report.parseError == true)
        #expect(report.rawText == "the model's raw, non-JSON reply text")
        #expect(report.scores.isEmpty)
        #expect(report.strengths.isEmpty)
        #expect(report.focusAreas.isEmpty)
        #expect(report.drillSuggestion == "")
    }

    /// Malformed-scores payload: `scores` arrives as a JSON object whose
    /// values aren't all integers (e.g. the coach model emitted a string
    /// where an Int score was expected). CoachReport.scores is typed
    /// `[String: Int]` with no custom decoding/normalization on the client
    /// side -- coercion/clamping now happens server-side, in
    /// coach.normalize_report (T5), before a report is ever sent, so this
    /// payload shape should never actually reach the client in practice.
    /// This model is still deliberately strict as a second line of defense:
    /// if a malformed payload ever did reach here (a bug elsewhere), it
    /// should fail loudly rather than silently coercing or dropping bad
    /// values client-side too.
    @Test func malformedScoresValueFailsToDecode() {
        let json = """
        {
            "scores": {"warmth": "great job"},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": null,
            "parse_error": null
        }
        """.data(using: .utf8)!

        #expect(throws: DecodingError.self) {
            try JSONDecoder().decode(CoachReport.self, from: json)
        }
    }

    /// Same malformed-scores intent, but with a non-integer numeric value
    /// (a float) rather than a string — Int's Decodable implementation
    /// rejects fractional JSON numbers, so this should also fail loudly.
    @Test func fractionalScoresValueFailsToDecode() {
        let json = """
        {
            "scores": {"warmth": 4.5},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": null,
            "parse_error": null
        }
        """.data(using: .utf8)!

        #expect(throws: DecodingError.self) {
            try JSONDecoder().decode(CoachReport.self, from: json)
        }
    }

    @Test func progressEntryDecodesAndUsesSessionIdAsIdentity() throws {
        let json = """
        {
            "session_id": "sess-123",
            "scenario_id": "coffee-shop",
            "created_at": "2026-07-10T12:00:00Z",
            "report": {
                "scores": {"warmth": 5},
                "strengths": [],
                "focus_areas": [],
                "drill_suggestion": "",
                "raw": null,
                "parse_error": null
            }
        }
        """.data(using: .utf8)!

        let entry = try JSONDecoder().decode(ProgressEntry.self, from: json)

        #expect(entry.sessionId == "sess-123")
        #expect(entry.id == entry.sessionId)
        #expect(entry.scenarioId == "coffee-shop")
        #expect(entry.createdAt == "2026-07-10T12:00:00Z")
        #expect(entry.report.scores == ["warmth": 5])
    }

    /// ProgressEntry's Hashable conformance is identity-based (by
    /// sessionId only), matching what SwiftUI's `navigationDestination`
    /// needs in ProgressListView — two entries with the same session id
    /// but different report contents are still considered equal/same-hash.
    @Test func progressEntryHashableIsSessionIdentityBased() {
        let reportA = CoachReport(scores: ["warmth": 1], strengths: [], focusAreas: [], drillSuggestion: "", rawText: nil, parseError: nil)
        let reportB = CoachReport(scores: ["warmth": 5], strengths: ["different"], focusAreas: [], drillSuggestion: "", rawText: nil, parseError: nil)

        let entryA = ProgressEntry(sessionId: "same-id", scenarioId: "a", createdAt: "t1", report: reportA)
        let entryB = ProgressEntry(sessionId: "same-id", scenarioId: "b", createdAt: "t2", report: reportB)

        #expect(entryA == entryB)
        #expect(entryA.hashValue == entryB.hashValue)
    }
}
