flowchart TD
    %% Recurring Process
    Start[Start Recurring Process]
    
    subgraph Pending_Review_Check[Find Pending Reviews]
        P1[Find All Resume Trackers with Status 'in_progress']
        P2[Group by Employee ID]
        P3[Get Notification Trackers]
    end
    
    subgraph Notification_Check[Process Each Employee]
        N1{Last Notification > 24h ago?}
        N2[Get All Pending Reviews]
        N3[Send Notification]
        N4[Update Notification Status]
        N5[Skip Employee]
        
        N1 -->|Yes| N2
        N1 -->|No| N5
        N2 --> N3
        N3 --> N4
    end
    
    Start --> P1
    P1 --> P2
    P2 --> P3
    P3 --> N1
    N4 --> End[End]
    N5 --> End

    %% Styling
    classDef default fill:white,stroke:#333,stroke-width:1px,color:black