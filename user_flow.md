flowchart TD
    %% Initial Load
    Start[User Clicks Email Link]
    A[Load Browser Interface]
    B[Call API: Get Pending Reviews]

    %% Query and Display
    subgraph Data_Load[Data Loading]
        C[Query Resume Trackers]
        D[Filter Status = 'in_progress']
        E[Display Projects and Descriptions]
    end

    %% User Actions
    subgraph User_Interface[User Interface]
        F{User Action?}
        G[Edit Description]
        H[Click Save]
        I[Click Discard]
        UI[Remove from UI]
    end

    %% Save Flow
    subgraph Save_Process[Save Process]
        S1[Set status = 'yes']
        S2[Update Description]
        S3[Update Resume]
        S4[Save Resume]
    end

    %% Discard Flow
    subgraph Discard_Process[Discard Process]
        D1[Set status = 'rejected']
    end

    End[End]

    %% Flow Connections
    Start --> A
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F

    F -->|Edit| G
    G --> F
    
    %% Save path with immediate UI update
    F -->|Save| H
    H --> UI
    UI --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> End
    
    %% Discard path with immediate UI update
    F -->|Discard| I
    I --> UI
    UI --> D1
    D1 --> End

    %% Style classes
    classDef default fill:#2f3136,stroke:#666,color:#fff