workspace "Greeting CLI" "Program Kit C4-aligned intake model" {
    model {
        maintainer = person "Local maintainer" "Runs the greeting command locally." "ProgramKitId:maintainer,ProgramKitType:person,ProgramKitStatus:explicit"
        greeting_operation = element "Greeting operation" "Module / Bridge" "Owns the complete command invocation, exact output, and invalid-argument behavior." "DomainModule,ProgramKitId:greeting-operation,ProgramKitType:domain-capability,ProgramKitStatus:proposed,ProgramKitOwner:Local maintainer"
        greeting_cli = softwareSystem "Greeting CLI" "Prints the exact Program Kit greeting and reports invalid arguments." "CommandLine,ProgramKitId:greeting-cli,ProgramKitType:software-system,ProgramKitStatus:explicit,ProgramKitOwner:Local maintainer"
        greeting_context = element "Greeting" "Bounded Context" "Candidate boundary for the complete greeting journey." "Domain,ProgramKitId:greeting-context,ProgramKitType:bounded-context,ProgramKitStatus:proposed,ProgramKitOwner:Local maintainer"
        maintainer_invokes_cli = maintainer -> greeting_cli "Invokes the greeting command" "Local process" "ProgramKitId:maintainer-invokes-cli,ProgramKitStatus:explicit"
        cli_delegates_greeting = greeting_cli -> greeting_operation "Delegates the validated invocation" "In-process call" "ProgramKitId:cli-delegates-greeting,ProgramKitStatus:proposed"
    }

    views {
        systemContext greeting_cli "system-context" {
            title "Greeting CLI System Context"
            description "The single local actor and software system."
            include maintainer greeting_cli
            exclude "relationship.tag==Relationship"
            include maintainer_invokes_cli
            autolayout lr
        }
        custom "domain-landscape" {
            title "Greeting domain landscape"
            description "The provisional classified greeting subdomain and context."
            include greeting_context
            autolayout lr
        }
        custom "context-map" {
            title "Greeting strategic Context Map"
            description "The single context has no cross-context dependencies."
            include greeting_context
            autolayout lr
        }
        custom "greeting-decomposition" {
            title "Greeting context modules"
            description "The context and its owned command module."
            include greeting_context greeting_operation
            autolayout lr
        }
        dynamic * "journey-greeting" {
            title "Invoke greeting command"
            description "The complete valid or invalid invocation journey."
            1: maintainer_invokes_cli "Invokes the greeting command"
            2: cli_delegates_greeting "Delegates the validated invocation"
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
