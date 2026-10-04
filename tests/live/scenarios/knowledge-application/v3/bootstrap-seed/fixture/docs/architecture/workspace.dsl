workspace "Equipment Lending Desk" "Program Kit C4-aligned intake model" {
    model {
        operator = person "Operator" "An operator reserves, confirms and cancels camera lending." "ProgramKitId:operator,ProgramKitType:person,ProgramKitStatus:explicit"
        lending_operation = element "Lending operation" "Module / Bridge" "Own camera reservation policy, explicit confirmation, cancellation, durable operation identity and retry ownership." "DomainModule,ProgramKitId:lending-operation,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:Operator"
        lending_system = softwareSystem "Equipment Lending Desk" "Own camera reservation policy, explicit confirmation, cancellation, durable operation identity and retry ownership." "ProgramKitId:lending-system,ProgramKitType:software-system,ProgramKitStatus:explicit,ProgramKitOwner:Operator"
        lending_context = element "Lending" "Bounded Context" "Own camera reservation policy, explicit confirmation, cancellation, durable operation identity and retry ownership." "Domain,ProgramKitId:lending-context,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:Operator"
        operator_requests_reservation = operator -> lending_system "Requests the reservation operation through the public V1 boundary." "HTTP JSON" "ProgramKitId:operator-requests-reservation,ProgramKitStatus:explicit"
        system_delegates_lending = lending_system -> lending_operation "Requests the reservation operation through the public V1 boundary." "HTTP JSON" "ProgramKitId:system-delegates-lending,ProgramKitStatus:proposed"
    }

    views {
        systemContext lending_system "system-context" {
            title "Equipment Lending Desk System Context"
            description "Equipment lending context and complete reservation journey."
            include operator lending_system
            exclude "relationship.tag==Relationship"
            include operator_requests_reservation
            autolayout lr
        }
        custom "domain-landscape" {
            title "Lending domain landscape"
            description "Equipment lending context and complete reservation journey."
            include lending_context
            autolayout lr
        }
        custom "context-map" {
            title "Lending strategic Context Map"
            description "Equipment lending context and complete reservation journey."
            include lending_context
            autolayout lr
        }
        custom "lending-decomposition" {
            title "Lending context modules"
            description "Equipment lending context and complete reservation journey."
            include lending_context lending_operation
            autolayout lr
        }
        dynamic * "journey-lending" {
            title "Invoke lending command"
            description "Equipment lending context and complete reservation journey."
            1: operator_requests_reservation "Requests the reservation operation through the public V1 boundary."
            2: system_delegates_lending "Requests the reservation operation through the public V1 boundary."
            autolayout lr
        }

        styles {
            element "Element" {
                shape RoundedBox
                background #F8FAFC
                color #172033
                stroke #94A3B8
                strokeWidth 2
                fontSize 22
            }
            element "Person" {
                shape Person
                background #0F766E
                color #FFFFFF
                stroke #115E59
                strokeWidth 2
            }
            element "Software System" {
                background #2563EB
                color #FFFFFF
                stroke #1D4ED8
                strokeWidth 2
            }
            element "ProgramKitType:bounded-context" {
                background #7C3AED
                color #FFFFFF
                stroke #6D28D9
                strokeWidth 2
            }
            element "ProgramKitType:domain-capability" {
                background #ECFDF5
                color #134E4A
                stroke #14B8A6
                strokeWidth 2
            }
            element "ProgramKitStatus:proposed" {
                stroke #F97316
                border dashed
            }
            relationship "Relationship" {
                color #475569
                thickness 3
                style solid
                routing Orthogonal
                fontSize 18
            }
            relationship "ProgramKitStatus:proposed" {
                color #EA580C
                style dashed
            }
        }
    }
}
