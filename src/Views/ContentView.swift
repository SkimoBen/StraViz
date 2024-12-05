//
//  ContentView.swift
//  RunViz
//
//  Created by Ben Pearman on 2024-11-23.
//

import SwiftUI
import HealthKit
import CoreLocation

struct ContentView: View {
    
    var body: some View {
        
        NavigationStack {
            WorkoutSelect()
        }
    }
}




struct WorkoutSelect: View {
    @State var workouts: [HKWorkout] = []
    
    var body: some View {
        List(workouts, id: \.uuid) { workout in
            NavigationLink(destination: WorkoutRouteDetailView(workout: workout)) {
                VStack(alignment: .leading) {
                    Text("Workout Sample type: \(workout.startDate)")
                    //Text("Workout description: \(workout.description)")
                }
            
            }
            
        }
        .onAppear {
            authorizeHealthKit()
            fetchWorkouts { fetchedWorkouts in
                self.workouts = fetchedWorkouts ?? []
            }
        }
        
    }
}



struct WorkoutRouteDetailView: View {
    @State var rawData: [RawData] = []
    var workout: HKWorkout
    @State private var locationSamples: [CLLocation] = []
    @State private var hrSamples: [HKQuantitySample] = []
    @State private var paceDistance: [PaceDistanceData] = []
    
    @State var is_loaded = false
    var body: some View {
        Text("Total HR Samples: \(hrSamples.count)")
        Text("Total location Samples: \(locationSamples.count)")
        Text("Total Pace Samples: \(paceDistance.count)")
        Button(action: {
            rawData = creatRawData(locationSamples: locationSamples, hrSamples: hrSamples, pdSamples: paceDistance)
        }, label: {
            Text("Make raw data")
        })
        NavigationLink(destination: NormalizedDataView(rawData: rawData)) {
            Text("View Normalized Data")
        }
        VStack {
            
            let minSamples = min(hrSamples.count, locationSamples.count)
            Text("Min Samples: \(minSamples)")
            if minSamples >= 1 {
                ScrollView {
                    ForEach(0..<minSamples, id: \.self) { i in
                        // This stupidity only exists so that i can put the hd in
                        let c_cords = locationSamples[i].coordinate
                        let hd: Double = {
                            if i > 0 {
                                let last_cord = locationSamples[i - 1].coordinate
                                return haversineDistance(lat1: c_cords.latitude, lon1: c_cords.longitude, lat2: last_cord.latitude, lon2: last_cord.longitude)
                            } else {
                                return 0.0
                            }
                        }()
                        VStack(alignment: .leading) {
                            
                            if rawData.count > 0 {
                                Spacer()
                                Spacer()
                                Text("RD: Displacement\(rawData[i].displacement)")
                                Text("RD: HR\(rawData[i].hr)")
      
                                Text("RD: altitude\(rawData[i].altitude)")
                                Text("RD: cords\(rawData[i].coords)")
                                Spacer()
                                Spacer()
                            }
                            
                            
                            Text("location Time: \(locationSamples[i].timestamp.formatted())")
                            Text("HR Time: \(hrSamples[i].startDate.formatted())")
                            Text("PD TIme: \(paceDistance[i].startTime.formatted())")
                            Spacer()
                            
                            Text("Altitude: \(Int(locationSamples[i].altitude))")
                            Text("Location: \(locationSamples[i].coordinate)")
                            Text("Distance: \(paceDistance[i].distance)km")
                            Text("Haversine Distance: \(hd)")
                            Text("Pace: \(1 / paceDistance[i].averagePace )min/k")
                            
                            Text("HR: \(Int(hrSamples[i].quantity.doubleValue(for: HKUnit(from: "count/min"))))")
                            Spacer()
                        }
                        Divider()
                        
                    }
                }
                .padding()
                
            }
        }
        
        .onAppear {
            
            if !is_loaded {
                fetchWorkoutRoute(for: workout) { workoutRoute in
                    queryRouteData(route: workoutRoute!) { locationData in
                        locationSamples.append(contentsOf: locationData)
    
                    }
                    
                }
                queryHeartRateData(for: workout) { quantitySamples in
                    hrSamples.append(contentsOf: quantitySamples ?? [])
                }
                
                getDistanceAndPaceIntervals(workout: workout) { pd in
                    paceDistance.append(contentsOf: pd)
                }
                 // create the list of raw data points
                
                is_loaded = true
            }
            
            
        }
        
        
    }
}



struct NormalizedDataView: View {
    @State private var normalizedWorkoutData: RunningWorkoutData? = nil
    var rawData: [RawData]
    
    var body: some View {
        VStack {
            if let normalizedData = normalizedWorkoutData {
                Text("Total Points: \(normalizedData.normPoints.count)")
                Button(action: {
                    let encoder = JSONEncoder()
                    encoder.outputFormatting = .prettyPrinted // For readable JSON
                    if let jsonData = try? encoder.encode(normalizedWorkoutData), let jsonString = String(data: jsonData, encoding: .utf8) {
                        print(jsonString)
                    }
                }, label: {
                    Text("Make JSON")
                })
                
                ScrollView {
                    ForEach(0..<normalizedData.normPoints.count, id: \.self) { i in
                        let point = normalizedData.normPoints[i]
                        VStack(alignment: .leading) {
                            Text("Point \(i + 1)")
                            Text("HR: \(point.HR)")
                            Text("Coordinates: (\(String(format: "%.2f", point.coordinates.0)), \(String(format: "%.2f", point.coordinates.1)))")
                            Text("Altitude from Zero: \(point.altitudeFromZero) m")
                            Divider()
                        }
                        .padding()
                    }
                }
            } else {
                Text("No normalized data available")
            }
        }
        .onAppear {
            normalizedWorkoutData = create_NormalizedWorkoutData(rawData: rawData)
            normalizedWorkoutData?.removeClosePoints(minDistance: 100.0)
        }
        .navigationTitle("Normalized Data")
        .padding()
    }
}



#Preview {
    ContentView()
}





