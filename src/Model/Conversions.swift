//
//  conversions.swift
//  RunViz
//
//  Created by Ben Pearman on 2024-11-24.
//

import CoreLocation

let earthRadius: Double = 6371000.0 // Earth's radius in meters

func clamp<T: Comparable>(_ value: T, _ minValue: T, _ maxValue: T) -> T {
    return min(max(value, minValue), maxValue)
}

func haversineDistance(lat1: Double, lon1: Double, lat2: Double, lon2: Double) -> Double {

    // Convert degrees to radians
    func degreesToRadians(_ degrees: Double) -> Double {
        return degrees * .pi / 180
    }

    let dLat = degreesToRadians(lat2 - lat1)
    let dLon = degreesToRadians(lon2 - lon1)

    let a = sin(dLat / 2) * sin(dLat / 2) +
            cos(degreesToRadians(lat1)) * cos(degreesToRadians(lat2)) *
            sin(dLon / 2) * sin(dLon / 2)

    let c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earthRadius * c
}

func degreesToRadians(_ degrees: Double) -> Double {
    return degrees * .pi / 180.0
}


// Function to convert GCS coordinates to Cartesian coordinates
func convertGCStoCartesian(starting_gc: CLLocationCoordinate2D, current_gc: CLLocationCoordinate2D) -> (x: Double, y: Double) {
    // Convert degrees to radians
    let startLatRad = degreesToRadians(starting_gc.latitude)
    let startLonRad = degreesToRadians(starting_gc.longitude)
    let currentLatRad = degreesToRadians(current_gc.latitude)
    let currentLonRad = degreesToRadians(current_gc.longitude)
    
    // Differences in coordinates
    let deltaLat = currentLatRad - startLatRad
    let deltaLon = currentLonRad - startLonRad
    
    // Compute Cartesian coordinates
    let x = earthRadius * deltaLon * cos((startLatRad + currentLatRad) / 2)
    let y = earthRadius * deltaLat
    
    return (x, y)
}

/// Normalizes a value from its original range to a specified target range.
///   - value: The value to normalize.
///   - min: The minimum value of the original range.
///   - max: The maximum value of the original range.
///   - toRange: A tuple `(rangeMin, rangeMax)` specifying the target range.
func normalize<T: FloatingPoint>(_ value: T, min: T, max: T, toRange range: (T, T)) -> T {
    let (rangeMin, rangeMax) = range
    guard max != min else {
        fatalError("The input range min and max cannot be the same.")
    }
    // Normalize value to 0-1
    let normalizedValue = (value - min) / (max - min)
    // Scale to target range
    return normalizedValue * (rangeMax - rangeMin) + rangeMin
}
