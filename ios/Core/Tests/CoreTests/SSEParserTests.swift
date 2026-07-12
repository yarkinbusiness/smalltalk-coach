import Testing
import Foundation
@testable import Core

struct SSEParserTests {
    @Test func parsesNormalDeltaLine() throws {
        let event = try SSEParser.parse(#"data: {"delta": "Hi there"}"#)
        #expect(event == .delta("Hi there"))
    }

    @Test func parsesDoneLine() throws {
        let event = try SSEParser.parse(#"data: {"done": true}"#)
        #expect(event == .done)
    }

    @Test func parsesErrorLine() throws {
        let event = try SSEParser.parse(#"data: {"error": "something broke"}"#)
        #expect(event == .error("something broke"))
    }

    /// Per `SSEParser.parse`'s documented check order (`done` first, then
    /// `error`, then `delta`), a payload carrying both `done` and `error`
    /// resolves to `.done` — `done == true` short-circuits before the
    /// `error` field is even consulted.
    @Test func doneTakesPrecedenceOverError() throws {
        let event = try SSEParser.parse(#"data: {"done": true, "error": "x"}"#)
        #expect(event == .done)
    }

    /// With no `done` field present, `error` is checked before `delta`, so
    /// a payload carrying both resolves to `.error`, not `.delta`.
    @Test func errorTakesPrecedenceOverDelta() throws {
        let event = try SSEParser.parse(#"data: {"error": "x", "delta": "y"}"#)
        #expect(event == .error("x"))
    }

    /// A line that doesn't carry the SSE `data: ` field prefix at all
    /// (e.g. a comment line, or some other SSE field like `event: ping`)
    /// isn't an error — the parser returns nil so the caller can skip it,
    /// matching the original `guard line.hasPrefix("data: ") else { continue }`
    /// behavior that used to live inline in APIClient.streamMessage.
    @Test func malformedNonDataLineReturnsNil() throws {
        #expect(try SSEParser.parse("not an sse line") == nil)
        #expect(try SSEParser.parse(": this is a comment") == nil)
        #expect(try SSEParser.parse("event: ping") == nil)
    }

    @Test func emptyLineReturnsNil() throws {
        #expect(try SSEParser.parse("") == nil)
    }

    /// `done == false` (explicitly present but false) should not be treated
    /// as a done event, and with no delta present the payload has nothing
    /// to yield.
    @Test func doneFalseWithNoDeltaReturnsNil() throws {
        let event = try SSEParser.parse(#"data: {"done": false}"#)
        #expect(event == nil)
    }

    /// A `data: ` line whose JSON body is invalid should propagate a
    /// decoding error rather than being silently swallowed as nil — this
    /// matches the original behavior where `try JSONDecoder().decode(...)`
    /// was unguarded and a bad payload would fail the whole stream.
    @Test func malformedJSONAfterDataPrefixThrows() {
        #expect(throws: DecodingError.self) {
            try SSEParser.parse("data: {not valid json")
        }
    }

    /// Empty JSON object after `data: ` decodes fine (both fields are
    /// optional) but yields nothing to the caller.
    @Test func emptyJSONObjectReturnsNil() throws {
        #expect(try SSEParser.parse("data: {}") == nil)
    }
}
