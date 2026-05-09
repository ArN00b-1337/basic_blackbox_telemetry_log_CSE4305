# Basic Flight Data Recorder — Black Box Simulator

A C program that simulates a simplified aircraft Black Box (Flight Data Recorder) using a **Doubly Linked List**. Built as a Data Structures assignment to demonstrate real-world application of bidirectional linked lists in aviation telemetry.

---

## About the Project

In aviation, a Flight Data Recorder continuously logs key parameters throughout a flight. When an incident occurs, investigators analyze this data — first forward to understand the timeline, then backward to trace the root cause.

This program replicates that process by:
- Storing flight records dynamically in a doubly linked list
- Displaying records in **forward order** (flight log)
- Replaying records in **reverse order** (crash analysis)

---

##  Built With

- **Language:** C
- **Concepts:** Doubly Linked List, Dynamic Memory Allocation, Pointer Manipulation

---


##  Sample Output

```
--- Flight Log (Forward Traversal) ---
T+10s | Altitude: 35000.0 | Speed: 450.0 | Pitch: 2.0
T+20s | Altitude: 28000.0 | Speed: 420.0 | Pitch: -5.0
T+30s | Altitude: 15000.0 | Speed: 390.0 | Pitch: -18.0
T+40s | Altitude: 500.0   | Speed: 310.0 | Pitch: -45.0

--- Crash Analysis (Backward Traversal) ---
T+40s | Altitude: 500.0   | Speed: 310.0 | Pitch: -45.0
T+30s | Altitude: 15000.0 | Speed: 390.0 | Pitch: -18.0
T+20s | Altitude: 28000.0 | Speed: 420.0 | Pitch: -5.0
T+10s | Altitude: 35000.0 | Speed: 450.0 | Pitch: 2.0

 Memory Cleared.
```

---

## Key Concepts Demonstrated

| Concept | Usage |
|---|---|
| Doubly Linked List | Stores flight records with `next` and `prev` pointers |
| Dynamic Allocation | `malloc()` used for each new flight record |
| Forward Traversal | Reconstructs full chronological flight log |
| Backward Traversal | Simulates investigator reverse crash analysis |
| Memory Deallocation | `free()` called on every node after use |

---

## Authors

> Arnob Chakraborty and Sadman Saif Brinto

---

This project was developed for academic purposes.
