//
//  ViewModel.swift
//  RunViz
//
//  Created by Ben Pearman on 2024-11-27.
//

import Foundation
import CoreLocation

//MARK: Normalized Data
/// Represents a single point in time during a run. These points are sampled every five minutes.
/// Coordinates are in meters from the starting point, on the x and y axis.
struct NormalizedData: Encodable {
    let HR: Int                         /// 0 - 10. Avg Heart rate
    let coordinates: (Double, Double)   /// The cartesian coordinates of current point.
    let altitudeFromZero: Int           /// Distance from the lowest altitude in meters.
    let realDistance: Double                /// distance travelled from previous point to current
    let pace: Double                    /// avg. pace (km / min) from previous point to current.

    // For turning the struct into JSON
    enum CodingKeys: String, CodingKey {
            case HR
            case coordinates
            case altitudeFromZero
            case realDistance
            case pace
        }

        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(HR, forKey: .HR)
            try container.encode(["x": coordinates.0, "y": coordinates.1], forKey: .coordinates)
            try container.encode(altitudeFromZero, forKey: .altitudeFromZero)
            try container.encode(realDistance, forKey: .realDistance)
            try container.encode(pace, forKey: .pace)
        }
}

//MARK: Class- Normalized Running Workout Data
class RunningWorkoutData: Encodable {
    // Min / Max values for calculations.
    let max_total_distance: Int = 300 /// KM's. Max run length
    let starting_cart_coords: (Float, Float) = (0.0, 0.0) /// (X,Y). Cartesian starting point.
    let min_point_distance: Float = 0.33 /// KM's. Minimum distance travelled between two points
    let max_point_distance: Float = 2.0 /// KM's. Max distance travelled between two points
    let min_pace: Float = 15.0 /// mins / KM. slowest pace between points
    let max_pace: Float = 2.5 /// mins / KM. fastest pace between two points
    
    // Calculated constants.
    var ttlDistance: Double /// The total recorded distance. This is used for Log scaling.
    let zeroAltitude: Int
    let startingCoordinates: CLLocationCoordinate2D
    var normPoints: [NormalizedData]
    
    
    // Coding keys
    enum CodingKeys: String, CodingKey {
        case ttlDistance
        case zeroAltitude
        case startingCoordinates
        case normPoints
    }
    
    init(
        ttlDistance: Double,
        zeroAltitude: Int,
        startingCoordinates: CLLocationCoordinate2D,
        points: [NormalizedData] = []
        
    ) {
        self.ttlDistance = ttlDistance
        self.zeroAltitude = zeroAltitude
        self.startingCoordinates = startingCoordinates
        self.normPoints = points
        
    }
    
    /// Remove points that are close together. This is to combat overlapping faces in the mesh.
    func removeClosePoints(minDistance: Double = 100.0) {
        // If there are fewer than 3 points I can't filter
        guard normPoints.count > 2 else { return }
        
        var filteredPoints: [NormalizedData] = [normPoints.first!] /// Always keep the first point
        
        for i in 1..<(normPoints.count - 1) {
            let currentPoint = normPoints[i]
            var isFarEnough = true
            
            for otherPoint in filteredPoints {
                let dx = currentPoint.coordinates.0 - otherPoint.coordinates.0
                let dy = currentPoint.coordinates.1 - otherPoint.coordinates.1
                let distance = sqrt(dx * dx + dy * dy)
                
                if distance < minDistance {
                    isFarEnough = false
                    break
                }
            }
            
            if isFarEnough {
                filteredPoints.append(currentPoint)
            }
        }
        
        filteredPoints.append(normPoints.last!) /// Always keep the last point
        normPoints = filteredPoints
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        try container.encode(ttlDistance, forKey: .ttlDistance)
        try container.encode(zeroAltitude, forKey: .zeroAltitude)
        try container.encode(["latitude": startingCoordinates.latitude, "longitude": startingCoordinates.longitude], forKey: .startingCoordinates)
        
        try container.encode(normPoints, forKey: .normPoints)
    }
    
    func pointsToJSON() -> String? {
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted // Optional for readable JSON

        do {
            let jsonData = try encoder.encode(normPoints)
            return String(data: jsonData, encoding: .utf8)
        } catch {
            print("Error encoding points to JSON: \(error)")
            return nil
        }
    }

}


//MARK: RawData Struct
///For storing each data point, which gets sampled every five minutes.
struct RawData {
    let hr: Int                         // Heart rate
    let displacement: Double            // displacement in KM's from the starting point (Straight line)
    let altitude: Float                 // Altitude in Meters
    let coords: CLLocationCoordinate2D  // Location (lat lon)
    let distance: Double  // Distance recorded from the current sample to the previous sample
    let pace: Double                    // km / min. Pace from previous sample to current.
}



