import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1 else {
    print("Usage: swift ocr.swift <image_path>")
    exit(1)
}

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {
    print("Failed to load image: \(imagePath)")
    exit(1)
}

let width = Double(cgImage.width)
let height = Double(cgImage.height)

let request = VNRecognizeTextRequest { (request, error) in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    
    var results: [[String: Any]] = []
    
    for observation in observations {
        guard let topCandidate = observation.topCandidates(1).first else { continue }
        
        let text = topCandidate.string
        let confidence = topCandidate.confidence
        
        // Vision coordinates are bottom-left origin (0.0 - 1.0)
        let boundingBox = observation.boundingBox
        
        let x = boundingBox.origin.x * 1000.0
        let y = (1.0 - boundingBox.origin.y - boundingBox.size.height) * 1000.0
        let w = boundingBox.size.width * 1000.0
        let h = boundingBox.size.height * 1000.0
        
        // Font size estimation in pt (canvas height = 540pt for 810px)
        let fontSizePt = (boundingBox.size.height * height) * (540.0 / height)
        
        let item: [String: Any] = [
            "text": text,
            "confidence": round(Double(confidence) * 100) / 100,
            "box_norm": [round(x * 10) / 10, round(y * 10) / 10, round(w * 10) / 10, round(h * 10) / 10],
            "estimated_font_size_pt": round(fontSizePt * 10) / 10
        ]
        results.append(item)
    }
    
    if let jsonData = try? JSONSerialization.data(withJSONObject: results, options: .prettyPrinted),
       let jsonString = String(data: jsonData, encoding: .utf8) {
        print(jsonString)
    }
}

request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
