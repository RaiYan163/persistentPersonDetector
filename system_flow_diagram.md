# Person Tracker System - Flow Diagram

## System Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN APPLICATION (main.py)                        │
│                         Central Orchestrator & Display                      │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRAME PROCESSING LOOP                               │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Camera    │───▶│   YOLO      │───▶│  MediaPipe  │───▶│   ReID      │  │
│  │   Input     │    │ Detection   │    │  Gestures   │    │  Features   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                   │                   │                   │      │
│         ▼                   ▼                   ▼                   ▼      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Frame     │    │ All People  │    │Pointing Up/ │    │ 512-dim     │  │
│  │  Capture    │    │ + Track IDs │    │ Victory     │    │ Features    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GESTURE LOGIC & SECURITY                                │
│                                                                             │
│  ┌─────────────────┐              ┌─────────────────┐                      │
│  │   NOT LOCKED    │              │     LOCKED      │                      │
│  │                 │              │                 │                      │
│  │ • Look for      │              │ • Look for      │                      │
│  │   Pointing Up   │              │   Victory       │                      │
│  │ • Associate to  │              │ • Validate from │                      │
│  │   Person        │              │   Locked Person │                      │
│  │ • Create Lock   │              │ • Unlock if     │                      │
│  │                 │              │   Valid         │                      │
│  └─────────────────┘              └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENT REID FILTERING                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    TARGET TRACKER (target_tracker.py)                  │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │ │
│  │  │  Person Profile │    │  Similarity     │    │  Security       │    │ │
│  │  │  Management     │    │  Matching       │    │  Validation     │    │ │
│  │  │                 │    │                 │    │                 │    │ │
│  │  │ • 512-dim       │    │ • Cosine        │    │ • High threshold│    │ │
│  │  │   Features      │    │   Similarity    │    │   (0.75+)       │    │ │
│  │  │ • Feature       │    │ • Multi-frame   │    │ • Spatial       │    │ │
│  │  │   History       │    │   Validation    │    │   Consistency   │    │ │
│  │  │ • Adaptive      │    │ • Profile       │    │ • Timeout       │    │ │
│  │  │   Updates       │    │   Updates       │    │   (15s)         │    │ │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DIRECTION CONTROL (if locked)                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                DIRECTION CONTROLLER (direction_controller.py)          │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐              ┌─────────────────┐                  │ │
│  │  │  Forward/       │              │  Left/Right     │                  │ │
│  │  │  Backward       │              │  Control        │                  │ │
│  │  │  (Gestures)     │              │  (Pose)         │                  │ │
│  │  │                 │              │                 │                  │ │
│  │  │ • Closed Fist   │              │ • Right Elbow   │                  │ │
│  │  │   = Forward     │              │   Angle         │                  │ │
│  │  │ • Thumb Up      │              │ • < 90° = Left  │                  │ │
│  │  │   = Backward    │              │ • > 90° = Right │                  │ │
│  │  │ • Open Palm     │              │ • Smoothing     │                  │ │
│  │  │   = Pause       │              │   (5 frames)    │                  │ │
│  │  └─────────────────┘              └─────────────────┘                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DISPLAY & GUI UPDATES                               │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Main Window   │    │ Direction GUI   │    │   User Input    │        │
│  │                 │    │                 │    │                 │        │
│  │ • Filtered      │    │ • Real-time     │    │ • 'q' = Quit    │        │
│  │   Detections    │    │   Commands      │    │ • 'r' = Reset   │        │
│  │ • Gesture       │    │ • Color-coded   │    │ • 'f' = Full    │        │
│  │   Visualization │    │   Status        │    │   Screen        │        │
│  │ • HUD Info      │    │ • Stays on Top  │    │                 │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
INPUT FRAME
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PARALLEL PROCESSING                              │
│                                                                             │
│  ┌─────────────────┐              ┌─────────────────┐                      │
│  │   YOLO          │              │   MediaPipe     │                      │
│  │   Detection     │              │   Gestures      │                      │
│  │                 │              │                 │                      │
│  │ • All People    │              │ • Pointing Up   │                      │
│  │ • Track IDs     │              │ • Victory       │                      │
│  │ • Bounding Boxes│              │ • Hand Landmarks│                      │
│  │ • Confidence    │              │ • Confidence    │                      │
│  └─────────────────┘              └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
    │                                      │
    ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GESTURE ASSOCIATION                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  For each gesture:                                                     │ │
│  │  1. Expand person bounding boxes by 40%                                │ │
│  │  2. Check if gesture point is inside expanded box                      │ │
│  │  3. If not found, find nearest person within 15% of frame diagonal     │ │
│  │  4. Associate gesture to person                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENT REID PROCESSING                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  If NOT LOCKED:                                                         │ │
│  │  • Look for pointing up gestures                                        │ │
│  │  • Extract ReID features from associated person                         │ │
│  │  • Create persistent person profile                                     │ │
│  │  • Set lock state                                                       │ │
│  │                                                                         │ │
│  │  If LOCKED:                                                             │ │
│  │  • Extract ReID features from all detected people                       │ │
│  │  • Compare with locked person profile (cosine similarity)               │ │
│  │  • Apply high confidence threshold (0.75+)                             │ │
│  │  • Validate spatial consistency                                         │ │
│  │  • Filter to show only matching person                                  │ │
│  │  • Update profile with high-confidence matches                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DIRECTION CONTROL (if locked)                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  • Crop locked person region from frame                                 │ │
│  │  • Run MediaPipe pose detection on crop                                 │ │
│  │  • Run MediaPipe gesture recognition on crop                            │ │
│  │  • Analyze right elbow angle for left/right                             │ │
│  │  • Analyze hand gestures for forward/backward                           │ │
│  │  • Apply smoothing and hold logic                                       │ │
│  │  • Update direction GUI                                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTPUT & DISPLAY                                    │
│                                                                             │
│  ┌─────────────────┐              ┌─────────────────┐                      │
│  │   Main Display  │              │ Direction GUI   │                      │
│  │                 │              │                 │                      │
│  │ • Filtered      │              │ • Forward/      │                      │
│  │   Detections    │              │   Backward      │                      │
│  │ • Gesture       │              │ • Left/Right    │                      │
│  │   Overlays      │              │ • Color-coded   │                      │
│  │ • Status HUD    │              │ • Real-time     │                      │
│  │ • Instructions  │              │   Updates       │                      │
│  └─────────────────┘              └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Flow Diagram

```
VICTORY GESTURE DETECTED
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY VALIDATION                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  1. ASSOCIATION CHECK                                                   │ │
│  │     • Find which person the victory gesture belongs to                  │ │
│  │     • Use expanded bounding box method                                  │ │
│  │     • Fallback to nearest person method                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  2. REID VALIDATION                                                     │ │
│  │     • Extract ReID features from associated person                      │ │
│  │     • Compare with locked person profile                                │ │
│  │     • Compute cosine similarity                                         │ │
│  │     • Check against high threshold (0.75+)                             │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  3. DECISION                                                            │ │
│  │     • If similarity >= 0.75: UNLOCK (valid victory from locked person) │ │
│  │     • If similarity < 0.75: IGNORE (victory from different person)     │ │
│  │     • Log security events for debugging                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN APPLICATION                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  PersonLockSystem                                                       │ │
│  │  • process_frame()                                                      │ │
│  │  • handle_gesture_logic()                                               │ │
│  │  • draw_frame()                                                         │ │
│  │  • handle_input()                                                       │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Person    │  │  Gesture    │  │   Target    │  │ Direction   │
│  Detector   │  │  Detector   │  │  Tracker    │  │ Controller  │
│             │  │             │  │             │  │             │
│ • YOLO      │  │ • MediaPipe │  │ • ReID      │  │ • Pose      │
│ • Tracking  │  │ • Gestures  │  │ • Profile   │  │ • Gestures  │
│ • Filtering │  │ • Landmarks │  │ • Security  │  │ • Commands  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Person    │  │    Utils    │  │ Direction   │  │    Config   │
│    ReID     │  │             │  │     GUI     │  │             │
│             │  │ • Drawing   │  │             │  │ • Constants │
│ • OSNet     │  │ • Distance  │  │ • Tkinter   │  │ • Colors    │
│ • Features  │  │ • BBox Ops  │  │ • Display   │  │ • Thresholds│
│ • Similarity│  │ • Assoc.    │  │ • Updates   │  │ • Settings  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```
