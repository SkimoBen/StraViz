//
//  HealthKit Model.swift
//  RunViz
//
//  Created by Ben Pearman on 2024-11-24.
//


import Foundation
import HealthKit
import CoreLocation


let healthStore = HKHealthStore()

//MARK: Authorization
func authorizeHealthKit() {
    let healthKitTypes: Set = [
        HKObjectType.quantityType(forIdentifier: .heartRate)!,
        HKObjectType.workoutType(),
        HKSeriesType.workoutRoute(),
        HKQuantityType.quantityType(forIdentifier: .distanceWalkingRunning)!
    ]

    healthStore.requestAuthorization(toShare: [], read: healthKitTypes) { _, _ in }
}

//MARK: Fetch all workouts of a certain workout type
func fetchWorkouts(completion: @escaping ([HKWorkout]?) -> Void) {
    let workoutPredicate = HKQuery.predicateForWorkouts(with: .running) // Change this based on the workout type
    let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)

    let query = HKSampleQuery(sampleType: .workoutType(), predicate: workoutPredicate, limit: HKObjectQueryNoLimit, sortDescriptors: [sortDescriptor]) { _, samples, _ in
        DispatchQueue.main.async {
            completion(samples as? [HKWorkout])
        }
    }

    healthStore.execute(query)
}



//MARK: Location queries. Get the WorkoutRoute object of a given workout
func fetchWorkoutRoute(for workout: HKWorkout, completion: @escaping (HKWorkoutRoute?) -> Void) {
    let predicate = HKQuery.predicateForObjects(from: workout)
    let query = HKAnchoredObjectQuery(type: HKSeriesType.workoutRoute(), predicate: predicate, anchor: nil, limit: HKObjectQueryNoLimit) { _, samples, _, _, _ in
        DispatchQueue.main.async {
            completion(samples?.first as? HKWorkoutRoute)
        }
    }

    healthStore.execute(query)
}


func queryHeartRateData(for workout: HKWorkout, completion: @escaping ([HKQuantitySample]?) -> Void) {
    guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }
    
    // Define the anchor and interval for the query
    let startDate = workout.startDate
    let endDate = workout.endDate
    let anchorDate = Calendar.current.startOfDay(for: startDate)
    let interval = DateComponents(minute: 5)
    
    let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)
    
    let query = HKStatisticsCollectionQuery(
        quantityType: heartRateType,
        quantitySamplePredicate: predicate,
        options: .discreteAverage,
        anchorDate: anchorDate,
        intervalComponents: interval
    )
    
    query.initialResultsHandler = { _, statisticsCollection, _ in
        var samples: [HKQuantitySample] = []
        
        if let statisticsCollection = statisticsCollection {
            statisticsCollection.enumerateStatistics(from: startDate, to: endDate) { statistics, _ in
                if let quantity = statistics.averageQuantity() {
                    let sample = HKQuantitySample(
                        type: heartRateType,
                        quantity: quantity,
                        start: statistics.startDate,
                        end: statistics.endDate
                    )
                    samples.append(sample)
                }
            }
        }
        
        DispatchQueue.main.async {
            completion(samples)
        }
    }
    
    healthStore.execute(query)
}


//MARK: get the location data from the workout route object, samples every 5 minutes.
func queryRouteData(route: HKWorkoutRoute, completion: @escaping ([CLLocation]) -> Void) {
    var allLocations: [CLLocation] = []
    var lastSampleTime: Date? = nil
    let samplingInterval: TimeInterval = 5 * 60 // 5 minutes in seconds

    let routeQuery = HKWorkoutRouteQuery(route: route) { _, locationsOrNil, isDone, _ in
        if let locations = locationsOrNil {
            for location in locations {
                if let lastSample = lastSampleTime {
                    if location.timestamp.timeIntervalSince(lastSample) >= samplingInterval {
                        allLocations.append(location)
                        lastSampleTime = location.timestamp
                        
                    }
                } else {
                    // Include the first location and set it as the last sampled time
                    allLocations.append(location)
                    lastSampleTime = location.timestamp
                }
            }
        }

        if isDone {
            DispatchQueue.main.async {
                completion(allLocations)
            }
        }
    }

    healthStore.execute(routeQuery)
}


struct PaceDistanceData {
    var startTime: Date
    var endTime: Date
    var distance: Double  // in km, the actual recorded distance (not straight line)
    var averagePace: Double  // in km/min
}

func getDistanceAndPaceIntervals(workout: HKWorkout, completion: @escaping ([PaceDistanceData]) -> Void) {
    let distanceType = HKQuantityType.quantityType(forIdentifier: .distanceWalkingRunning)!
    
    // Predicate to get samples during the workout
    let predicate = HKQuery.predicateForSamples(withStart: workout.startDate, end: workout.endDate, options: .strictStartDate)
    
    // Set interval to 5 minutes
    var intervalComponents = DateComponents()
    intervalComponents.minute = 5
    
    // Use the workout's start date as the anchor date
    let anchorDate = workout.startDate
    
    let statisticsOptions: HKStatisticsOptions = .cumulativeSum
    
    // Create the statistics collection query
    let query = HKStatisticsCollectionQuery(quantityType: distanceType,
                                            quantitySamplePredicate: predicate,
                                            options: statisticsOptions,
                                            anchorDate: anchorDate,
                                            intervalComponents: intervalComponents)
    
    query.initialResultsHandler = { query, statisticsCollection, error in
        if let error = error {
            print("Error fetching statistics: \(error.localizedDescription)")
            completion([])
            return
        }
        
        var intervals: [PaceDistanceData] = []
        
        if let statisticsCollection = statisticsCollection {
     
            statisticsCollection.enumerateStatistics(from: workout.startDate, to: workout.endDate) { (statistics, stop) in
                let startDate = statistics.startDate
                let endDate = statistics.endDate
                let duration = endDate.timeIntervalSince(startDate)
                
                if let sumQuantity = statistics.sumQuantity() {
                    let distance = sumQuantity.doubleValue(for: HKUnit.meterUnit(with: .kilo))  // Distance in kilometers
                    let averagePace = distance > 0 ? distance / (duration / 60.0) : 0.0  // km per minute
                    
                    
                    let intervalData = PaceDistanceData(startTime: startDate,
                                                        endTime: endDate,
                                                        distance: distance,
                                                        averagePace: averagePace)
                    intervals.append(intervalData)
                } else {
                    print("No sum quantity for interval from \(startDate) to \(endDate)")
                }
            }
            // print("Total intervals found: \(intervals.count)")
        } else {
            print("StatisticsCollection is nil")
        }
        completion(intervals)
    }
    

    healthStore.execute(query)
}


