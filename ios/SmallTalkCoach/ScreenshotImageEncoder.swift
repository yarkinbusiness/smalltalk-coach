import Foundation
import UIKit

struct ScreenshotUploadPayload: Equatable {
    let data: Data
    let mediaType: String

    var base64Encoded: String { data.base64EncodedString() }
}

enum ScreenshotImageEncoder {
    static let compressionThresholdBytes = 8 * 1024 * 1024

    static func needsJPEGRecompression(rawByteCount: Int) -> Bool {
        rawByteCount > compressionThresholdBytes
    }

    static func prepare(data: Data, mediaType: String) throws -> ScreenshotUploadPayload {
        let backendSupportedTypes: Set<String> = ["image/png", "image/jpeg", "image/webp"]
        guard !needsJPEGRecompression(rawByteCount: data.count), backendSupportedTypes.contains(mediaType) else {
            guard let image = UIImage(data: data), let jpeg = image.jpegData(compressionQuality: 0.8) else {
                throw ScreenshotImageEncodingError.couldNotReadImage
            }
            return ScreenshotUploadPayload(data: jpeg, mediaType: "image/jpeg")
        }
        return ScreenshotUploadPayload(data: data, mediaType: mediaType)
    }
}

enum ScreenshotImageEncodingError: LocalizedError, Equatable {
    case couldNotReadImage

    var errorDescription: String? {
        "We couldn’t read that image. Please choose another screenshot."
    }
}
