//
//  Data Creation.swift
//  RunViz
//
//  Created by Ben Pearman on 2024-11-29.
//

import CoreLocation
import HealthKit

/// Creates raw workout data by combining location samples and heart rate samples.
func creatRawData(locationSamples: [CLLocation], hrSamples: [HKQuantitySample], pdSamples: [PaceDistanceData]) -> [RawData] {
    let minSamples = min(locationSamples.count, hrSamples.count)

    var rawData: [RawData] = []
    guard let startingPoint = locationSamples.first else {
            // Return an empty array if there are no location samples
            return rawData
    }
    
    
    for i in 0..<minSamples {
        
        let location = locationSamples[i]
        let hr = Int(hrSamples[i].quantity.doubleValue(for: HKUnit(from: "count/min")))
        let displacement = startingPoint.distance(from: location)
        let altitude = Float(location.altitude)
        let coords = location.coordinate
        let distance = pdSamples[i].distance
        let pace = pdSamples[i].averagePace
        
        rawData.append(RawData(hr: hr, displacement: displacement, altitude: altitude, coords: coords, distance: distance, pace: pace))
    }

    return rawData
}

/// Creates a normalized workout dataset from raw data.
///
/// This function processes raw workout data and normalizes the heart rate, coordinates, and altitude.
/// It converts geographic coordinates to a Cartesian system and computes relative altitude values, returning a
/// structured `RunningWorkoutData` object containing normalized data points.
///
func create_NormalizedWorkoutData(rawData: [RawData]) -> RunningWorkoutData? {
    let data_len = rawData.count
    
    guard let minAltitude = rawData.map({$0.altitude}).min() else {
        return nil
    }
    guard let startGC = rawData.first?.coords else {
        return nil
    }
    var ttlDistance = 0.0
    for i in 0..<rawData.count {
        ttlDistance += rawData[i].distance
    }
            
    // Create the Run Object, this will be my container for normalization.
    let runData = RunningWorkoutData(ttlDistance: ttlDistance, zeroAltitude: Int(minAltitude), startingCoordinates: startGC)
    
    // Loop through the raw data points.
    for i in 0...data_len-1 {
        
        // Calculate the normalized data points
        let hr = clamp(Float(rawData[i].hr), 130, 175)
        let norm_hr = normalize(hr, min: 130, max: 175, toRange: (0,10))
        let norm_cords = convertGCStoCartesian(starting_gc: runData.startingCoordinates, current_gc: rawData[i].coords)
        let norm_altitude = Int(rawData[i].altitude) - runData.zeroAltitude
        let norm_distance = rawData[i].distance /// In meters, still raw.
        let norm_pace = rawData[i].pace         /// In Km / min. Raw.
        
        // Create the struct
        let normalizedDataPoint = NormalizedData(HR: Int(norm_hr), coordinates: norm_cords, altitudeFromZero: norm_altitude, realDistance: norm_distance, pace: norm_pace)
        
        // Add the struct to the RunningWorkoutData class.
        runData.normPoints.append(normalizedDataPoint)
        
    }
    
    return runData
}
