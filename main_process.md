flowchart TD
    %% Input Section
    A[Project Key Member Entry]

    %% Event Processing Section
    subgraph Event_Processing[Event Processing]
        D[Store Event in project_key_members]
        E{Get Tracker}
        F[Create New Tracker]
        G[Update Existing Tracker]
        
        E -->|Not Found| F
        E -->|Exists| G
        F --> H
        G --> H
    end

    %% Update Decision Section
    subgraph Update_Decision[Update Decision]
        H{Hours >= 40?}
        I{Status = 'no'?}
        J[Set status to 'in_progress']
        K[Update Hours Only]
        
        H -->|No| K
        H -->|Yes| I
        I -->|No| K
        I -->|Yes| J
    end

    %% Resume Update Process Section
    subgraph Resume_Update[Resume Update Process]
        R1[Get Resume Data]
        R2[Get Project Data]
        R3[Generate Project Experience]
        R4[Update Tracker Description]
        
        R1 --> R2
        R2 --> R3
        R3 --> R4
    end

    %% Immediate Notification Process
    subgraph Notification[Notification Process]
        N1[Get/Create Notification Tracker]
        N2[Send Notification]
        N3[Update Notification Status]
        
        N1 --> N2
        N2 --> N3

    end

    %% Main Flow
    A --> D
    D --> E
    J --> R1
    R4 --> N1
    K --> End[End]
    N3 --> End

    %% Styling
    classDef default fill:white,stroke:#333,stroke-width:1px,color:black